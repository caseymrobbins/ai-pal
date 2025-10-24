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
)
from .interfaces import (
    IPersonalityModuleConnector,
    IARIConnector,
    IDashboardConnector,
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
