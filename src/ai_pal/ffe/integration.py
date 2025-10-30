"""
FFE Integration with AC-AI Framework

Maps FFE components to existing Phase 1-3 systems:

Phase 1 Integration:
- Gate System: FFE enhances Humanity Gate (Gate #2) scoring
- AHO Tribunal: FFE provides non-exploitative design evidence

Phase 2 Integration:
- ARI Monitor: Growth Scaffold uses ARI for bottleneck detection
- EDM Monitor: Quality scoring for atomic blocks
- Self-Improvement Loop: Feeds FFE effectiveness data

Phase 3 Integration:
- Enhanced Context Manager: Stores personality profiles as memories
- Privacy Manager: Respects user privacy in win sharing
- Multi-Model Orchestrator: AI responses for reframing
- Agency Dashboard: Displays FFE metrics

This module provides concrete implementations of FFE integration connectors.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Set
from pathlib import Path
from dataclasses import dataclass

from loguru import logger

# Import existing AC-AI components
from ..context.enhanced_context import (
    EnhancedContextManager,
    MemoryEntry,
    MemoryType,
    MemoryPriority,
)
from ..monitoring.ari_monitor import ARIMonitor, AgencyTrend
from ..monitoring.edm_monitor import EDMMonitor
from ..privacy.advanced_privacy import AdvancedPrivacyManager
from ..orchestration.multi_model import (
    MultiModelOrchestrator,
    TaskRequirements,
    TaskComplexity,
    OptimizationGoal,
)
from ..ui.agency_dashboard import AgencyDashboard

# Import FFE models
from .models import (
    PersonalityProfile,
    SignatureStrength,
    StrengthType,
    BottleneckTask,
    BottleneckReason,
    FFEMetrics,
    TimeBlockSize,
)
from .interfaces import (
    IPersonalityModuleConnector,
    IARIConnector,
    IDashboardConnector,
    IGrowthScaffold,
)


# ============================================================================
# PERSONALITY MODULE CONNECTOR (Phase 3 - Context Manager)
# ============================================================================

class PersonalityModuleConnector(IPersonalityModuleConnector):
    """
    Connects FFE to EnhancedContextManager for personality storage

    Stores personality profiles as specialized memory entries:
    - Core values → PREFERENCE memories with tag "core_value"
    - Life goals → GOAL memories
    - Signature strengths → SKILL memories with tag "signature_strength"
    - Priorities → GOAL memories with tag "current_priority"
    """

    def __init__(self, context_manager: EnhancedContextManager):
        """
        Initialize connector

        Args:
            context_manager: EnhancedContextManager instance from Phase 3
        """
        self.context_manager = context_manager
        logger.info("PersonalityModuleConnector initialized")

    async def load_personality_profile(self, user_id: str) -> PersonalityProfile:
        """
        Load user's personality profile from context memories

        Reconstructs PersonalityProfile from various memory types.
        """
        logger.debug(f"Loading personality profile for user {user_id}")

        profile = PersonalityProfile(user_id=user_id)

        # Load core values (PREFERENCE memories with tag "core_value")
        value_memories = await self.context_manager.search_memories(
            user_id=user_id,
            query="",
            memory_types=[MemoryType.PREFERENCE],
            tags={"core_value"},
            limit=50
        )
        profile.core_values = [m.content for m in value_memories]

        # Load life goals (GOAL memories)
        goal_memories = await self.context_manager.search_memories(
            user_id=user_id,
            query="",
            memory_types=[MemoryType.GOAL],
            tags={"life_goal"},
            limit=50
        )
        profile.life_goals = [m.content for m in goal_memories]

        # Load current priorities (GOAL memories with tag "current_priority")
        priority_memories = await self.context_manager.search_memories(
            user_id=user_id,
            query="",
            memory_types=[MemoryType.GOAL],
            tags={"current_priority"},
            limit=20
        )
        profile.current_priorities = [m.content for m in priority_memories]

        # Load signature strengths (SKILL memories with tag "signature_strength")
        strength_memories = await self.context_manager.search_memories(
            user_id=user_id,
            query="",
            memory_types=[MemoryType.SKILL],
            tags={"signature_strength"},
            limit=10
        )

        for mem in strength_memories:
            # Parse strength from memory metadata
            strength_type_str = mem.metadata.get("strength_type", "analytical")
            try:
                strength_type = StrengthType(strength_type_str)
            except ValueError:
                strength_type = StrengthType.ANALYTICAL

            strength = SignatureStrength(
                strength_id=mem.memory_id,
                strength_type=strength_type,
                identity_label=mem.content,
                strength_description=mem.metadata.get("description", ""),
                confidence_score=mem.relevance_score,
                usage_count=mem.access_count,
                last_used=mem.last_accessed,
            )
            profile.signature_strengths.append(strength)

        # Determine primary strength (most frequently used)
        if profile.signature_strengths:
            primary = max(profile.signature_strengths, key=lambda s: s.usage_count)
            profile.primary_strength = primary.strength_type

        logger.info(
            f"Loaded personality profile for {user_id}: "
            f"{len(profile.core_values)} values, "
            f"{len(profile.signature_strengths)} strengths, "
            f"{len(profile.current_priorities)} priorities"
        )

        return profile

    async def save_personality_profile(self, profile: PersonalityProfile) -> bool:
        """
        Save updated personality profile to context manager

        Stores profile components as specialized memories.
        """
        logger.debug(f"Saving personality profile for user {profile.user_id}")

        try:
            # Save core values as PREFERENCE memories
            for value in profile.core_values:
                await self.context_manager.add_memory(
                    user_id=profile.user_id,
                    content=value,
                    memory_type=MemoryType.PREFERENCE,
                    priority=MemoryPriority.HIGH,
                    tags={"core_value", "personality_profile"}
                )

            # Save life goals as GOAL memories
            for goal in profile.life_goals:
                await self.context_manager.add_memory(
                    user_id=profile.user_id,
                    content=goal,
                    memory_type=MemoryType.GOAL,
                    priority=MemoryPriority.HIGH,
                    tags={"life_goal", "personality_profile"}
                )

            # Save current priorities as GOAL memories
            for priority in profile.current_priorities:
                await self.context_manager.add_memory(
                    user_id=profile.user_id,
                    content=priority,
                    memory_type=MemoryType.GOAL,
                    priority=MemoryPriority.CRITICAL,
                    tags={"current_priority", "personality_profile"}
                )

            # Save signature strengths as SKILL memories
            for strength in profile.signature_strengths:
                await self.context_manager.add_memory(
                    user_id=profile.user_id,
                    content=strength.identity_label,
                    memory_type=MemoryType.SKILL,
                    priority=MemoryPriority.HIGH,
                    tags={"signature_strength", "personality_profile"},
                    metadata={
                        "strength_type": strength.strength_type.value,
                        "description": strength.strength_description,
                        "confidence": strength.confidence_score,
                    }
                )

            logger.info(f"Saved personality profile for {profile.user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save personality profile: {e}")
            return False

    async def update_strength(
        self,
        user_id: str,
        strength: SignatureStrength
    ) -> bool:
        """
        Update a signature strength after use

        Increments usage count and updates last_used timestamp.
        """
        logger.debug(f"Updating strength {strength.strength_type} for {user_id}")

        try:
            # Find existing strength memory
            strength_memories = await self.context_manager.search_memories(
                user_id=user_id,
                query=strength.identity_label,
                memory_types=[MemoryType.SKILL],
                tags={"signature_strength"},
                limit=1
            )

            if strength_memories:
                memory = strength_memories[0]
                # Update metadata
                memory.metadata["usage_count"] = strength.usage_count
                memory.metadata["last_used"] = strength.last_used.isoformat() if strength.last_used else None

                # Update via context manager (would need update_memory method)
                # For now, just increment access count
                memory.access_count = strength.usage_count
                memory.last_accessed = strength.last_used or datetime.now()

                logger.info(f"Updated strength {strength.strength_type} (uses: {strength.usage_count})")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update strength: {e}")
            return False


# ============================================================================
# ARI CONNECTOR (Phase 2 - ARI Monitor)
# ============================================================================

class ARIConnector(IARIConnector):
    """
    Connects FFE Growth Scaffold to ARI Monitor for bottleneck detection

    Uses ARI alerts and trends to identify:
    - Tasks user avoids (skill atrophy)
    - Tasks causing agency loss
    - Tasks with declining competence
    """

    def __init__(self, ari_monitor: ARIMonitor):
        """
        Initialize connector

        Args:
            ari_monitor: ARIMonitor instance from Phase 2
        """
        self.ari_monitor = ari_monitor
        logger.info("ARIConnector initialized")

    async def detect_skill_atrophy(
        self,
        user_id: str,
        lookback_days: int = 30
    ) -> List[str]:
        """
        Detect skills that are atrophying from ARI data

        Args:
            user_id: User to analyze
            lookback_days: How far back to look

        Returns:
            List of skill/task categories being avoided
        """
        logger.debug(f"Detecting skill atrophy for {user_id}")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # Get ARI report for period
        report = self.ari_monitor.generate_report(user_id, start_date, end_date)

        atrophying_skills = []

        # Check for skill atrophy alerts
        for alert in report.alerts:
            if "atrophy" in alert.lower() or "skill" in alert.lower():
                # Extract skill category from alert message
                # Format: "Skill atrophy detected in category: <category>"
                if "category:" in alert:
                    category = alert.split("category:")[-1].strip()
                    atrophying_skills.append(category)

        # Check for declining skill trend
        if report.skill_trend == "declining":
            # Get recent snapshots to identify specific skills
            if user_id in self.ari_monitor.snapshots:
                recent = self.ari_monitor.snapshots[user_id][-10:]  # Last 10 snapshots

                # Look for tasks with declining skill_after < skill_before
                for snapshot in recent:
                    if snapshot.skill_development < 0:  # Negative skill development
                        task_type = snapshot.task_type
                        if task_type not in atrophying_skills:
                            atrophying_skills.append(task_type)

        logger.info(f"Detected {len(atrophying_skills)} atrophying skills for {user_id}")
        return atrophying_skills

    async def get_avoided_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get tasks user is avoiding from ARI tracking

        Returns:
            List of avoided task dicts with metadata
        """
        logger.debug(f"Getting avoided tasks for {user_id}")

        avoided_tasks = []

        if user_id not in self.ari_monitor.snapshots:
            return avoided_tasks

        # Analyze snapshot history for patterns
        snapshots = self.ari_monitor.snapshots[user_id]

        # Track task types and their frequencies
        task_frequency: Dict[str, int] = {}
        task_last_seen: Dict[str, datetime] = {}

        for snapshot in snapshots:
            task_type = snapshot.task_type
            task_frequency[task_type] = task_frequency.get(task_type, 0) + 1
            task_last_seen[task_type] = snapshot.timestamp

        # Identify tasks that haven't been done recently
        now = datetime.now()
        all_task_types = set(task_frequency.keys())

        for task_type in all_task_types:
            last_seen = task_last_seen[task_type]
            days_since = (now - last_seen).days

            # If task hasn't been done in 14+ days, consider it avoided
            if days_since >= 14:
                avoided_tasks.append({
                    "task_type": task_type,
                    "last_done": last_seen,
                    "days_since": days_since,
                    "total_completions": task_frequency[task_type],
                    "reason": BottleneckReason.AVOIDED.value
                })

        logger.info(f"Found {len(avoided_tasks)} avoided tasks for {user_id}")
        return avoided_tasks


# ============================================================================
# DASHBOARD CONNECTOR (Phase 3 - Agency Dashboard)
# ============================================================================

class DashboardConnector(IDashboardConnector):
    """
    Connects FFE metrics to Agency Dashboard

    Adds FFE section to dashboard showing:
    - Momentum loop statistics
    - Earned wins and pride hits
    - Bottleneck resolution progress
    - Humanity Gate contribution
    """

    def __init__(self, dashboard: AgencyDashboard):
        """
        Initialize connector

        Args:
            dashboard: AgencyDashboard instance from Phase 3
        """
        self.dashboard = dashboard
        logger.info("DashboardConnector initialized")

    async def get_ffe_metrics(
        self,
        user_id: str,
        period_days: int = 7
    ) -> Dict[str, Any]:
        """
        Get FFE metrics for dashboard display

        Args:
            user_id: User to get metrics for
            period_days: Reporting period

        Returns:
            Dict of FFE metrics
        """
        logger.debug(f"Getting FFE metrics for {user_id}, period={period_days} days")

        # This would query FFE's internal metrics storage
        # For now, return structure showing what would be displayed

        metrics = {
            "user_id": user_id,
            "period_days": period_days,
            "momentum_loops": {
                "total_completed": 0,
                "successful": 0,
                "success_rate": 0.0,
            },
            "atomic_blocks": {
                "total_completed": 0,
                "strength_tasks": 0,
                "growth_tasks": 0,
                "average_duration_minutes": 0,
            },
            "bottlenecks": {
                "detected": 0,
                "resolved": 0,
                "resolution_rate": 0.0,
                "active_queue_size": 0,
            },
            "pride_engagement": {
                "total_pride_hits": 0,
                "average_intensity": 0.0,
                "strongest_strength_used": None,
            },
            "autonomy_respect": {
                "five_block_stops_honored": 0,
                "user_modifications": 0,
                "user_initiated_tasks": 0,
            },
            "humanity_gate": {
                "ffe_contribution": 0.0,  # How much FFE boosts Gate #2 score
                "non_exploitative_score": 0.0,
                "autonomy_score": 0.0,
            },
        }

        return metrics

    async def format_ffe_dashboard_section(
        self,
        metrics: Dict[str, Any]
    ) -> str:
        """
        Format FFE data for dashboard text display

        Args:
            metrics: FFE metrics dict

        Returns:
            Formatted text for dashboard
        """
        lines = []
        lines.append("\n🔁 FRACTAL FLOW ENGINE (FFE):")

        # Momentum loops
        loops = metrics.get("momentum_loops", {})
        lines.append(f"  Momentum Loops: {loops.get('total_completed', 0)} completed")
        lines.append(f"  Success Rate: {loops.get('success_rate', 0.0):.1%}")

        # Atomic blocks
        blocks = metrics.get("atomic_blocks", {})
        lines.append(f"  Atomic Blocks: {blocks.get('total_completed', 0)} completed")
        lines.append(f"    - Strength Tasks: {blocks.get('strength_tasks', 0)}")
        lines.append(f"    - Growth Tasks: {blocks.get('growth_tasks', 0)}")

        # Bottlenecks
        bottlenecks = metrics.get("bottlenecks", {})
        lines.append(f"  Bottlenecks Resolved: {bottlenecks.get('resolved', 0)}/{bottlenecks.get('detected', 0)}")

        # Pride engagement
        pride = metrics.get("pride_engagement", {})
        lines.append(f"  Pride Hits: {pride.get('total_pride_hits', 0)}")
        lines.append(f"  Avg Intensity: {pride.get('average_intensity', 0.0):.2f}")

        # Humanity Gate contribution
        gate = metrics.get("humanity_gate", {})
        lines.append(f"  Humanity Gate Boost: +{gate.get('ffe_contribution', 0.0):.1f} points")

        return "\n".join(lines)


# ============================================================================
# HUMANITY GATE INTEGRATION
# ============================================================================

async def calculate_ffe_humanity_gate_contribution(
    ffe_metrics: FFEMetrics
) -> float:
    """
    Calculate how much FFE boosts Humanity Gate (Gate #2) score

    FFE provides evidence of:
    - Non-exploitative design (positive loops, not negative reinforcement)
    - Autonomy respect (5-Block Stop rule, user-initiated tasks)
    - Competence building (bottleneck resolution, growth tasks)
    - Pride-based (not shame/fear) motivation

    Args:
        ffe_metrics: FFE metrics for user

    Returns:
        Score contribution (0-30 points) for Humanity Gate
    """
    score = 0.0

    # Non-exploitative design (0-10 points)
    # Based on positive pride hits vs negative reinforcement
    if ffe_metrics.total_pride_hits > 0:
        pride_score = min(10.0, ffe_metrics.average_pride_intensity * 10)
        score += pride_score

    # Autonomy respect (0-10 points)
    # Based on 5-Block Stops honored and user modifications
    if ffe_metrics.five_block_stops_honored > 0:
        score += 5.0
    if ffe_metrics.user_plan_modifications > 0:
        score += 5.0

    # Competence building (0-10 points)
    # Based on bottleneck resolution and growth task completion
    if ffe_metrics.bottleneck_resolution_rate > 0.5:
        score += min(10.0, ffe_metrics.bottleneck_resolution_rate * 10)

    logger.info(
        f"FFE Humanity Gate contribution: {score:.1f}/30 "
        f"(pride: {ffe_metrics.total_pride_hits}, "
        f"bottlenecks resolved: {ffe_metrics.bottlenecks_resolved})"
    )

    return min(30.0, score)


# ============================================================================
# MULTI-MODEL ORCHESTRATOR INTEGRATION
# ============================================================================

async def get_ffe_ai_task_requirements() -> TaskRequirements:
    """
    Get task requirements for FFE AI operations

    FFE uses the Multi-Model Orchestrator for:
    - Scoping agent decisions (80/20 analysis)
    - Strength-based reframing
    - Reward message generation
    - Bottleneck analysis

    These require moderate reasoning but should be fast and cheap.
    """
    return TaskRequirements(
        task_complexity=TaskComplexity.MODERATE,
        min_reasoning_capability=0.75,  # Need good reasoning for reframing
        max_cost_per_1k_tokens=0.005,   # Keep costs low (high frequency)
        max_latency_ms=2000,             # Fast response for good UX
        requires_local_execution=False,
    )


# ============================================================================
# ADVANCED ARI-FFE INTEGRATION
# ============================================================================


@dataclass
class BottleneckSeverity:
    """
    Severity assessment for a detected bottleneck
    """
    severity_score: float  # 0-1, higher = more severe
    urgency: str  # "low", "medium", "high", "critical"

    # Contributing factors
    skill_gap: float
    avoidance_frequency: float
    agency_impact: float
    time_since_last_attempt: float

    # Recommendations
    recommended_priority: int  # Lower = higher priority
    suggested_reframe_intensity: float  # How strong should reframe be?


class RealTimeBottleneckDetector:
    """
    Real-time bottleneck detection from ARI snapshots

    Unlike batch-based detection, this monitors ARI snapshots as they arrive
    and immediately creates bottleneck tasks when thresholds are exceeded.

    Features:
    - Real-time monitoring of ARI snapshots
    - Automatic bottleneck creation on threshold violations
    - Severity calculation for prioritization
    - Auto-queueing to Growth Scaffold
    """

    def __init__(
        self,
        ari_monitor: ARIMonitor,
        growth_scaffold: IGrowthScaffold,
        skill_loss_threshold: float = -0.15,
        agency_loss_threshold: float = -0.1,
        high_reliance_threshold: float = 0.9,
    ):
        """
        Initialize real-time detector

        Args:
            ari_monitor: ARI Monitor to watch
            growth_scaffold: Growth Scaffold to queue bottlenecks to
            skill_loss_threshold: Create bottleneck if skill_development below this
            agency_loss_threshold: Create bottleneck if delta_agency below this
            high_reliance_threshold: Create bottleneck if ai_reliance above this
        """
        self.ari_monitor = ari_monitor
        self.growth_scaffold = growth_scaffold
        self.skill_loss_threshold = skill_loss_threshold
        self.agency_loss_threshold = agency_loss_threshold
        self.high_reliance_threshold = high_reliance_threshold

        # Track what we've already created bottlenecks for
        self.created_bottlenecks: Set[str] = set()  # task_type+user_id combos

        logger.info(
            f"RealTimeBottleneckDetector initialized "
            f"(skill_loss: {skill_loss_threshold}, "
            f"agency_loss: {agency_loss_threshold}, "
            f"high_reliance: {high_reliance_threshold})"
        )

    async def analyze_snapshot(
        self,
        snapshot: 'AgencySnapshot'
    ) -> Optional[BottleneckTask]:
        """
        Analyze a single ARI snapshot and create bottleneck if needed

        Args:
            snapshot: Newly recorded agency snapshot

        Returns:
            Created BottleneckTask if thresholds exceeded, else None
        """
        logger.debug(
            f"Analyzing snapshot for {snapshot.user_id} - "
            f"task: {snapshot.task_type}, "
            f"skill_dev: {snapshot.skill_development:.2f}, "
            f"agency: {snapshot.delta_agency:.2f}, "
            f"ai_reliance: {snapshot.ai_reliance:.2f}"
        )

        # Check if this task+user combo already has a bottleneck
        bottleneck_key = f"{snapshot.user_id}:{snapshot.task_type}"
        if bottleneck_key in self.created_bottlenecks:
            logger.debug(f"Bottleneck already exists for {bottleneck_key}, skipping")
            return None

        # Determine if bottleneck should be created
        bottleneck_reason = None

        if snapshot.skill_development < self.skill_loss_threshold:
            bottleneck_reason = BottleneckReason.SKILL_DEFICIT
            logger.info(
                f"Skill loss detected: {snapshot.skill_development:.2f} < {self.skill_loss_threshold}"
            )
        elif snapshot.delta_agency < self.agency_loss_threshold:
            bottleneck_reason = BottleneckReason.ANXIETY_INDUCING
            logger.info(
                f"Agency loss detected: {snapshot.delta_agency:.2f} < {self.agency_loss_threshold}"
            )
        elif snapshot.ai_reliance > self.high_reliance_threshold:
            bottleneck_reason = BottleneckReason.DEPENDENCY
            logger.info(
                f"High AI reliance detected: {snapshot.ai_reliance:.2f} > {self.high_reliance_threshold}"
            )

        if bottleneck_reason is None:
            # No bottleneck detected
            return None

        # Create bottleneck task
        severity = self._calculate_severity(snapshot)

        bottleneck = BottleneckTask(
            user_id=snapshot.user_id,
            task_description=f"Task type: {snapshot.task_type}",
            task_category=snapshot.task_type,
            bottleneck_reason=bottleneck_reason,
            detection_method="real_time_ari_monitor",
            avoidance_count=1,
            last_avoided=snapshot.timestamp,
            importance_score=self._estimate_importance(snapshot),
            skill_gap_severity=severity.skill_gap,
            queued=True,
            queued_date=datetime.now(),
        )

        # Queue to Growth Scaffold
        await self.growth_scaffold.queue_bottleneck(bottleneck)

        # Remember we created this
        self.created_bottlenecks.add(bottleneck_key)

        logger.info(
            f"Created bottleneck {bottleneck.bottleneck_id} for {snapshot.task_type} "
            f"(severity: {severity.severity_score:.2f}, urgency: {severity.urgency})"
        )

        return bottleneck

    def _calculate_severity(
        self,
        snapshot: 'AgencySnapshot'
    ) -> BottleneckSeverity:
        """
        Calculate severity of bottleneck from snapshot metrics

        Args:
            snapshot: Agency snapshot

        Returns:
            BottleneckSeverity assessment
        """
        # Skill gap: how far is skill_after below ideal (1.0)?
        skill_gap = max(0.0, 1.0 - snapshot.user_skill_after)

        # Avoidance: inferred from low autonomy + high AI reliance
        avoidance_frequency = (snapshot.ai_reliance + (1.0 - snapshot.autonomy_retention)) / 2.0

        # Agency impact: magnitude of agency loss
        agency_impact = max(0.0, -snapshot.delta_agency)

        # Time factor: not available in single snapshot, default to 0
        time_since_last_attempt = 0.0

        # Overall severity: weighted combination
        severity_score = (
            0.4 * skill_gap +
            0.3 * avoidance_frequency +
            0.2 * agency_impact +
            0.1 * time_since_last_attempt
        )

        # Determine urgency level
        if severity_score >= 0.8:
            urgency = "critical"
            priority = 1
        elif severity_score >= 0.6:
            urgency = "high"
            priority = 2
        elif severity_score >= 0.4:
            urgency = "medium"
            priority = 3
        else:
            urgency = "low"
            priority = 4

        # Suggested reframe intensity: higher severity = gentler reframe
        # (We don't want to overwhelm user with hard tasks when they're struggling)
        suggested_reframe_intensity = max(0.3, 1.0 - severity_score)

        return BottleneckSeverity(
            severity_score=severity_score,
            urgency=urgency,
            skill_gap=skill_gap,
            avoidance_frequency=avoidance_frequency,
            agency_impact=agency_impact,
            time_since_last_attempt=time_since_last_attempt,
            recommended_priority=priority,
            suggested_reframe_intensity=suggested_reframe_intensity,
        )

    def _estimate_importance(self, snapshot: 'AgencySnapshot') -> float:
        """
        Estimate importance of task from snapshot

        Tasks with higher task_efficacy potential are more important.

        Args:
            snapshot: Agency snapshot

        Returns:
            Importance score (0-1)
        """
        # Use task_efficacy as proxy for importance
        # High efficacy = important task worth doing well
        return min(1.0, max(0.0, snapshot.task_efficacy))

    async def start_monitoring(self) -> None:
        """
        Start monitoring ARI snapshots in background

        Note: This would need to be implemented as a background task
        that watches for new snapshots being added to ari_monitor.
        For now, this is a placeholder for future async monitoring.
        """
        logger.info("Real-time bottleneck monitoring started")
        # Future: asyncio.create_task to monitor snapshots
        pass

    def reset_created_bottlenecks(self, user_id: Optional[str] = None) -> None:
        """
        Reset tracking of created bottlenecks

        Args:
            user_id: If provided, only reset for this user
        """
        if user_id:
            self.created_bottlenecks = {
                key for key in self.created_bottlenecks
                if not key.startswith(f"{user_id}:")
            }
            logger.info(f"Reset bottleneck tracking for user {user_id}")
        else:
            self.created_bottlenecks.clear()
            logger.info("Reset all bottleneck tracking")


class AdaptiveDifficultyScaler:
    """
    Adaptive difficulty scaling based on ARI metrics

    Uses user's skill development trends, AI reliance, and agency retention
    to calculate optimal task difficulty - the "Goldilocks zone" where
    tasks are challenging but not overwhelming.

    Features:
    - Analyzes skill trends from ARI data
    - Recommends task complexity adjustments
    - Suggests time block sizes
    - Prevents skill atrophy through strategic difficulty
    """

    def __init__(
        self,
        ari_monitor: ARIMonitor,
        lookback_days: int = 14,
    ):
        """
        Initialize adaptive difficulty scaler

        Args:
            ari_monitor: ARI Monitor for accessing metrics
            lookback_days: How many days of history to analyze
        """
        self.ari_monitor = ari_monitor
        self.lookback_days = lookback_days
        logger.info(f"AdaptiveDifficultyScaler initialized (lookback: {lookback_days} days)")

    async def calculate_optimal_difficulty(
        self,
        user_id: str,
        task_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate optimal task difficulty for user

        Args:
            user_id: User to calculate for
            task_category: Optional specific task category to analyze

        Returns:
            Dict with difficulty recommendations
        """
        logger.debug(f"Calculating optimal difficulty for {user_id}")

        # Get recent ARI data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        report = self.ari_monitor.generate_report(user_id, start_date, end_date)

        # Get recent snapshots
        if user_id not in self.ari_monitor.snapshots:
            logger.warning(f"No snapshots found for user {user_id}")
            return self._default_difficulty_settings()

        snapshots = self.ari_monitor.snapshots[user_id]
        recent = [
            s for s in snapshots
            if s.timestamp >= start_date
        ]

        if task_category:
            recent = [s for s in recent if s.task_type == task_category]

        if not recent:
            logger.warning(f"No recent snapshots for {user_id} in category {task_category}")
            return self._default_difficulty_settings()

        # Calculate trends
        avg_skill_development = sum(s.skill_development for s in recent) / len(recent)
        avg_ai_reliance = sum(s.ai_reliance for s in recent) / len(recent)
        avg_autonomy = sum(s.autonomy_retention for s in recent) / len(recent)
        avg_agency = sum(s.delta_agency for s in recent) / len(recent)

        # Determine difficulty adjustments
        difficulty = self._calculate_goldilocks_difficulty(
            avg_skill_development,
            avg_ai_reliance,
            avg_autonomy,
            avg_agency,
        )

        logger.info(
            f"Optimal difficulty for {user_id}: {difficulty['complexity_level']} complexity, "
            f"{difficulty['time_block_size']} blocks "
            f"(skill_dev: {avg_skill_development:.2f}, reliance: {avg_ai_reliance:.2f})"
        )

        return difficulty

    def _calculate_goldilocks_difficulty(
        self,
        avg_skill_development: float,
        avg_ai_reliance: float,
        avg_autonomy: float,
        avg_agency: float,
    ) -> Dict[str, Any]:
        """
        Calculate "Goldilocks" difficulty - not too hard, not too easy

        Args:
            avg_skill_development: Average skill development trend
            avg_ai_reliance: Average AI reliance
            avg_autonomy: Average autonomy retention
            avg_agency: Average agency change

        Returns:
            Difficulty settings dict
        """
        # Calculate overall performance score (0-1)
        # Higher = user doing well = can handle more difficulty
        performance_score = (
            0.3 * max(0, min(1, (avg_skill_development + 0.2) / 0.4)) +  # Normalize skill dev
            0.3 * (1.0 - avg_ai_reliance) +  # Less reliance = better
            0.2 * avg_autonomy +
            0.2 * max(0, min(1, (avg_agency + 0.1) / 0.2))  # Normalize agency
        )

        # Determine complexity level
        if performance_score >= 0.75:
            complexity = "challenging"
            complexity_level = 4
        elif performance_score >= 0.55:
            complexity = "moderate"
            complexity_level = 3
        elif performance_score >= 0.35:
            complexity = "comfortable"
            complexity_level = 2
        else:
            complexity = "easy"
            complexity_level = 1

        # Determine time block size
        # Lower performance = smaller blocks (less overwhelming)
        if performance_score >= 0.7:
            time_block = TimeBlockSize.LARGE  # 90 min
        elif performance_score >= 0.5:
            time_block = TimeBlockSize.MEDIUM  # 45 min
        elif performance_score >= 0.3:
            time_block = TimeBlockSize.SMALL  # 25 min
        else:
            time_block = TimeBlockSize.TINY  # 15 min

        # Calculate growth vs comfort ratio
        # Higher performance = more growth tasks acceptable
        growth_ratio = min(0.5, max(0.1, performance_score * 0.6))
        comfort_ratio = 1.0 - growth_ratio

        return {
            "performance_score": performance_score,
            "complexity": complexity,
            "complexity_level": complexity_level,
            "time_block_size": time_block,
            "growth_task_ratio": growth_ratio,
            "comfort_task_ratio": comfort_ratio,
            "recommendation": self._generate_difficulty_recommendation(
                performance_score,
                avg_skill_development,
                avg_ai_reliance,
            ),
        }

    def _generate_difficulty_recommendation(
        self,
        performance_score: float,
        avg_skill_development: float,
        avg_ai_reliance: float,
    ) -> str:
        """
        Generate human-readable difficulty recommendation

        Args:
            performance_score: Overall performance score
            avg_skill_development: Average skill development
            avg_ai_reliance: Average AI reliance

        Returns:
            Recommendation text
        """
        if performance_score >= 0.75:
            return (
                "User is excelling - increase challenge level with growth tasks. "
                "Skills are developing well and AI reliance is healthy."
            )
        elif performance_score >= 0.55:
            return (
                "User is performing well - maintain current difficulty with "
                "balanced mix of comfort and growth tasks."
            )
        elif performance_score >= 0.35:
            if avg_ai_reliance > 0.7:
                return (
                    "User showing high AI reliance - reduce difficulty and "
                    "focus on building confidence with strength-based tasks."
                )
            elif avg_skill_development < -0.1:
                return (
                    "Skills declining - reduce task complexity and focus on "
                    "rebuilding fundamentals with smaller blocks."
                )
            else:
                return (
                    "User needs support - use smaller time blocks and "
                    "comfortable tasks to rebuild momentum."
                )
        else:
            return (
                "User struggling - minimize difficulty with tiny blocks and "
                "focus exclusively on strength-based tasks. Avoid growth tasks "
                "until confidence rebuilds."
            )

    def _default_difficulty_settings(self) -> Dict[str, Any]:
        """
        Return default difficulty settings when no data available

        Returns:
            Default settings dict
        """
        return {
            "performance_score": 0.5,
            "complexity": "moderate",
            "complexity_level": 3,
            "time_block_size": TimeBlockSize.SMALL,
            "growth_task_ratio": 0.3,
            "comfort_task_ratio": 0.7,
            "recommendation": "No historical data available - starting with moderate difficulty and small time blocks.",
        }


class SkillAtrophyPrevention:
    """
    Proactive skill atrophy prevention system

    Monitors skills for early signs of decline and suggests "touch-base"
    practice tasks before significant atrophy occurs (30-day threshold).

    Features:
    - Early detection of skill decline trends
    - Proactive practice task suggestions
    - Skill trend visualization data
    - Integration with Growth Scaffold for queuing
    """

    def __init__(
        self,
        ari_monitor: ARIMonitor,
        growth_scaffold: IGrowthScaffold,
        warning_days: int = 14,  # Warn if skill unused for this long
        critical_days: int = 30,  # Critical if unused for this long
    ):
        """
        Initialize skill atrophy prevention

        Args:
            ari_monitor: ARI Monitor for skill tracking
            growth_scaffold: Growth Scaffold for queueing practice tasks
            warning_days: Days before warning about unused skill
            critical_days: Days before critical atrophy alert
        """
        self.ari_monitor = ari_monitor
        self.growth_scaffold = growth_scaffold
        self.warning_days = warning_days
        self.critical_days = critical_days

        logger.info(
            f"SkillAtrophyPrevention initialized "
            f"(warning: {warning_days} days, critical: {critical_days} days)"
        )

    async def detect_declining_skills(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Detect skills showing decline trends

        Args:
            user_id: User to analyze

        Returns:
            List of declining skill dicts with metadata
        """
        logger.debug(f"Detecting declining skills for {user_id}")

        if user_id not in self.ari_monitor.snapshots:
            return []

        snapshots = self.ari_monitor.snapshots[user_id]

        # Group snapshots by task type (proxy for skill)
        task_snapshots: Dict[str, List['AgencySnapshot']] = {}
        for snapshot in snapshots:
            task_type = snapshot.task_type
            if task_type not in task_snapshots:
                task_snapshots[task_type] = []
            task_snapshots[task_type].append(snapshot)

        declining_skills = []
        now = datetime.now()

        for task_type, task_snaps in task_snapshots.items():
            # Sort by timestamp
            task_snaps.sort(key=lambda s: s.timestamp)

            # Get last snapshot
            last_snap = task_snaps[-1]
            days_since = (now - last_snap.timestamp).days

            # Calculate skill trend (last 5 snapshots)
            recent = task_snaps[-5:]
            if len(recent) >= 2:
                # Compare early vs late skill levels
                early_skill = sum(s.user_skill_after for s in recent[:len(recent)//2]) / (len(recent)//2)
                late_skill = sum(s.user_skill_after for s in recent[len(recent)//2:]) / (len(recent) - len(recent)//2)
                skill_change = late_skill - early_skill
            else:
                skill_change = 0.0

            # Check for decline
            is_declining = skill_change < -0.1
            is_unused = days_since >= self.warning_days
            is_critical = days_since >= self.critical_days

            if is_declining or is_unused:
                declining_skills.append({
                    "skill_category": task_type,
                    "days_since_use": days_since,
                    "skill_change": skill_change,
                    "last_skill_level": last_snap.user_skill_after,
                    "status": "critical" if is_critical else "warning" if is_unused else "declining",
                    "practice_urgency": self._calculate_practice_urgency(
                        days_since, skill_change, last_snap.user_skill_after
                    ),
                })

        # Sort by practice urgency (descending)
        declining_skills.sort(key=lambda s: s["practice_urgency"], reverse=True)

        logger.info(f"Found {len(declining_skills)} declining skills for {user_id}")
        return declining_skills

    def _calculate_practice_urgency(
        self,
        days_since: int,
        skill_change: float,
        current_level: float,
    ) -> float:
        """
        Calculate urgency of practicing this skill (0-1)

        Args:
            days_since: Days since last use
            skill_change: Recent skill trend
            current_level: Current skill level

        Returns:
            Urgency score (0-1)
        """
        # Time component: higher if unused longer
        time_urgency = min(1.0, days_since / self.critical_days)

        # Decline component: higher if declining faster
        decline_urgency = min(1.0, max(0.0, -skill_change / 0.3))

        # Level component: higher urgency if skill was previously high
        # (losing a high-level skill is worse than losing a low-level one)
        level_urgency = current_level

        # Combined urgency
        urgency = (
            0.4 * time_urgency +
            0.4 * decline_urgency +
            0.2 * level_urgency
        )

        return min(1.0, urgency)

    async def generate_practice_suggestions(
        self,
        user_id: str,
        max_suggestions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate practice task suggestions for declining skills

        Args:
            user_id: User to generate suggestions for
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of practice suggestion dicts
        """
        declining = await self.detect_declining_skills(user_id)

        suggestions = []
        for skill in declining[:max_suggestions]:
            suggestion = {
                "skill_category": skill["skill_category"],
                "urgency": skill["practice_urgency"],
                "suggested_task": f"Touch-base practice: {skill['skill_category']}",
                "time_block_size": TimeBlockSize.SMALL,  # Keep it low-pressure
                "rationale": self._generate_practice_rationale(skill),
            }
            suggestions.append(suggestion)

        logger.info(f"Generated {len(suggestions)} practice suggestions for {user_id}")
        return suggestions

    def _generate_practice_rationale(self, skill: Dict[str, Any]) -> str:
        """
        Generate explanation for why practice is suggested

        Args:
            skill: Skill info dict

        Returns:
            Rationale text
        """
        days = skill["days_since_use"]
        status = skill["status"]

        if status == "critical":
            return (
                f"It's been {days} days since you practiced {skill['skill_category']}. "
                f"A quick touch-base session would help prevent skill atrophy."
            )
        elif status == "warning":
            return (
                f"It's been {days} days since working on {skill['skill_category']}. "
                f"A brief practice session would keep this skill fresh."
            )
        else:  # declining
            return (
                f"Your {skill['skill_category']} skill has shown a slight decline recently. "
                f"A focused practice session could help rebuild confidence."
            )

    async def queue_practice_tasks(
        self,
        user_id: str,
        max_tasks: int = 2
    ) -> List[BottleneckTask]:
        """
        Queue practice tasks for declining skills to Growth Scaffold

        Args:
            user_id: User to queue tasks for
            max_tasks: Maximum tasks to queue

        Returns:
            List of queued BottleneckTask objects
        """
        suggestions = await self.generate_practice_suggestions(user_id, max_tasks)

        queued_tasks = []
        for suggestion in suggestions:
            # Create bottleneck task for practice
            bottleneck = BottleneckTask(
                user_id=user_id,
                task_description=suggestion["suggested_task"],
                task_category=suggestion["skill_category"],
                bottleneck_reason=BottleneckReason.AVOIDED,
                detection_method="skill_atrophy_prevention",
                avoidance_count=0,  # Not technically avoided, just unused
                last_avoided=None,
                importance_score=suggestion["urgency"],
                skill_gap_severity=suggestion["urgency"],
                queued=True,
                queued_date=datetime.now(),
            )

            await self.growth_scaffold.queue_bottleneck(bottleneck)
            queued_tasks.append(bottleneck)

            logger.info(
                f"Queued practice task for {suggestion['skill_category']} "
                f"(urgency: {suggestion['urgency']:.2f})"
            )

        return queued_tasks

    async def get_skill_trends(
        self,
        user_id: str,
        task_category: str
    ) -> Dict[str, Any]:
        """
        Get skill trend data for visualization

        Args:
            user_id: User to analyze
            task_category: Specific skill/task category

        Returns:
            Trend data dict suitable for graphing
        """
        if user_id not in self.ari_monitor.snapshots:
            return {"error": "No data available"}

        snapshots = [
            s for s in self.ari_monitor.snapshots[user_id]
            if s.task_type == task_category
        ]

        if not snapshots:
            return {"error": f"No data for category {task_category}"}

        # Sort by time
        snapshots.sort(key=lambda s: s.timestamp)

        # Extract trend data
        timestamps = [s.timestamp.isoformat() for s in snapshots]
        skill_levels = [s.user_skill_after for s in snapshots]
        skill_developments = [s.skill_development for s in snapshots]

        # Calculate overall trend
        if len(skill_levels) >= 2:
            trend_slope = (skill_levels[-1] - skill_levels[0]) / len(skill_levels)
        else:
            trend_slope = 0.0

        return {
            "task_category": task_category,
            "data_points": len(snapshots),
            "timestamps": timestamps,
            "skill_levels": skill_levels,
            "skill_developments": skill_developments,
            "trend_slope": trend_slope,
            "trend_direction": "improving" if trend_slope > 0.05 else "declining" if trend_slope < -0.05 else "stable",
            "current_level": skill_levels[-1] if skill_levels else 0.0,
            "days_since_last": (datetime.now() - snapshots[-1].timestamp).days if snapshots else 999,
        }
