"""
Dynamic Personality Updates Connector

Automatically refines personality profile based on:
- Task completion patterns
- Win analysis (what led to success)
- Struggle patterns (what was difficult)
- Preference observations
- Skill development trajectory

Updates strength confidence scores dynamically without requiring
explicit user input.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..models import SignatureStrength, StrengthType, AtomicBlock, GoalPacket
from .personality_discovery import PersonalityDiscoveryModule, UsagePattern


@dataclass
class StrengthEvidence:
    """Evidence for or against a strength"""
    strength_type: StrengthType
    evidence_type: str              # task_success, preference, struggle, etc.
    evidence_description: str
    confidence_impact: float        # +/- adjustment to confidence
    observed_at: datetime
    source: str                     # Where evidence came from


class DynamicPersonalityConnector:
    """
    Dynamically updates personality profile based on actual usage.

    Observes user behavior and automatically adjusts:
    - Strength confidence scores
    - Discovered new strengths
    - Preferred task types
    - Learning patterns
    """

    def __init__(
        self,
        personality_discovery: PersonalityDiscoveryModule,
        confidence_adjustment_rate: float = 0.05
    ):
        """
        Initialize Dynamic Personality Connector

        Args:
            personality_discovery: PersonalityDiscoveryModule to update
            confidence_adjustment_rate: How much to adjust per observation (0.01-0.1)
        """
        self.discovery = personality_discovery
        self.adjustment_rate = confidence_adjustment_rate

        # Track user strengths
        self._user_strengths: Dict[str, List[SignatureStrength]] = {}

        # Evidence buffer
        self._evidence_buffer: Dict[str, List[StrengthEvidence]] = {}

    # ===== AUTOMATIC UPDATES FROM FFE =====

    async def observe_task_completion(
        self,
        user_id: str,
        task: AtomicBlock,
        completion_quality: float,      # 0-1, how well completed
        user_enjoyment: Optional[float] = None,  # 0-1, optional
        time_taken: Optional[float] = None       # minutes
    ) -> List[StrengthEvidence]:
        """
        Observe task completion and infer strength usage

        Args:
            user_id: User who completed task
            task: Task that was completed
            completion_quality: How well it was done
            user_enjoyment: How much user enjoyed it
            time_taken: Time taken in minutes

        Returns:
            List of strength evidence inferred
        """
        evidence_list = []

        # Analyze task type to infer which strengths were used
        task_description = task.description.lower()

        # Check for analytical tasks
        if any(word in task_description for word in ["analyze", "debug", "solve", "research", "understand"]):
            if completion_quality > 0.7:
                evidence = StrengthEvidence(
                    strength_type=StrengthType.ANALYTICAL,
                    evidence_type="task_success",
                    evidence_description=f"Successfully completed analytical task: {task.title}",
                    confidence_impact=self.adjustment_rate * completion_quality,
                    observed_at=datetime.utcnow(),
                    source="task_completion"
                )
                evidence_list.append(evidence)

        # Check for creative tasks
        if any(word in task_description for word in ["design", "create", "brainstorm", "innovate", "imagine"]):
            if completion_quality > 0.7:
                evidence = StrengthEvidence(
                    strength_type=StrengthType.CREATIVE,
                    evidence_type="task_success",
                    evidence_description=f"Successfully completed creative task: {task.title}",
                    confidence_impact=self.adjustment_rate * completion_quality,
                    observed_at=datetime.utcnow(),
                    source="task_completion"
                )
                evidence_list.append(evidence)

        # Check for social tasks
        if any(word in task_description for word in ["collaborate", "present", "discuss", "team", "meet"]):
            if completion_quality > 0.7:
                evidence = StrengthEvidence(
                    strength_type=StrengthType.SOCIAL,
                    evidence_type="task_success",
                    evidence_description=f"Successfully completed social task: {task.title}",
                    confidence_impact=self.adjustment_rate * completion_quality,
                    observed_at=datetime.utcnow(),
                    source="task_completion"
                )
                evidence_list.append(evidence)

        # Check for practical/hands-on tasks
        if any(word in task_description for word in ["build", "implement", "code", "fix", "practice"]):
            if completion_quality > 0.7:
                evidence = StrengthEvidence(
                    strength_type=StrengthType.PRACTICAL,
                    evidence_type="task_success",
                    evidence_description=f"Successfully completed practical task: {task.title}",
                    confidence_impact=self.adjustment_rate * completion_quality,
                    observed_at=datetime.utcnow(),
                    source="task_completion"
                )
                evidence_list.append(evidence)

        # If user enjoyed it, boost confidence more
        if user_enjoyment and user_enjoyment > 0.7:
            for evidence in evidence_list:
                evidence.confidence_impact *= 1.2  # 20% boost for enjoyment

        # Store evidence
        if user_id not in self._evidence_buffer:
            self._evidence_buffer[user_id] = []
        self._evidence_buffer[user_id].extend(evidence_list)

        return evidence_list

    async def observe_task_struggle(
        self,
        user_id: str,
        task: AtomicBlock,
        struggle_reason: str,
        gave_up: bool = False
    ) -> List[StrengthEvidence]:
        """
        Observe task struggle/avoidance

        Struggles can reveal strength mismatches.

        Args:
            user_id: User who struggled
            task: Task they struggled with
            struggle_reason: Why they struggled
            gave_up: Whether they gave up

        Returns:
            Strength evidence (possibly negative)
        """
        evidence_list = []

        task_description = task.description.lower()

        # If struggled with analytical task, might not be analytical strength
        if any(word in task_description for word in ["analyze", "debug", "solve"]):
            if gave_up:
                evidence = StrengthEvidence(
                    strength_type=StrengthType.ANALYTICAL,
                    evidence_type="task_struggle",
                    evidence_description=f"Struggled with analytical task: {task.title}",
                    confidence_impact=-self.adjustment_rate * 0.5,  # Small negative adjustment
                    observed_at=datetime.utcnow(),
                    source="task_struggle"
                )
                evidence_list.append(evidence)

        # Similar for other types...

        if user_id not in self._evidence_buffer:
            self._evidence_buffer[user_id] = []
        self._evidence_buffer[user_id].extend(evidence_list)

        return evidence_list

    async def observe_goal_achievement(
        self,
        user_id: str,
        goal: GoalPacket,
        achievement_quality: float
    ) -> List[StrengthEvidence]:
        """
        Observe goal achievement

        Goal completion often reveals dominant strengths.

        Args:
            user_id: User who achieved goal
            goal: Goal that was achieved
            achievement_quality: Quality of achievement (0-1)

        Returns:
            Strength evidence
        """
        evidence_list = []

        # Analyze goal to infer strengths used
        goal_description = goal.description.lower()

        # Strategic planning goals
        if any(word in goal_description for word in ["plan", "strategy", "roadmap", "organize"]):
            evidence = StrengthEvidence(
                strength_type=StrengthType.STRATEGIC,
                evidence_type="goal_achievement",
                evidence_description=f"Achieved strategic goal: {goal.description}",
                confidence_impact=self.adjustment_rate * achievement_quality * 1.5,  # Goals worth more
                observed_at=datetime.utcnow(),
                source="goal_achievement"
            )
            evidence_list.append(evidence)

        # Learning goals show curiosity
        if any(word in goal_description for word in ["learn", "understand", "explore", "discover"]):
            evidence = StrengthEvidence(
                strength_type=StrengthType.CURIOUS,
                evidence_type="goal_achievement",
                evidence_description=f"Achieved learning goal: {goal.description}",
                confidence_impact=self.adjustment_rate * achievement_quality * 1.5,
                observed_at=datetime.utcnow(),
                source="goal_achievement"
            )
            evidence_list.append(evidence)

        if user_id not in self._evidence_buffer:
            self._evidence_buffer[user_id] = []
        self._evidence_buffer[user_id].extend(evidence_list)

        return evidence_list

    async def observe_preference(
        self,
        user_id: str,
        preference_type: str,
        preference_value: Any,
        strength_implications: Optional[Dict[StrengthType, float]] = None
    ):
        """
        Observe user preference

        Preferences can indicate strengths.

        Args:
            user_id: User expressing preference
            preference_type: Type of preference
            preference_value: The preference
            strength_implications: How this maps to strengths
        """
        if not strength_implications:
            return

        evidence_list = []

        for strength_type, confidence_impact in strength_implications.items():
            evidence = StrengthEvidence(
                strength_type=strength_type,
                evidence_type="preference",
                evidence_description=f"Preference: {preference_type} = {preference_value}",
                confidence_impact=confidence_impact * self.adjustment_rate * 0.5,  # Preferences less strong signal
                observed_at=datetime.utcnow(),
                source="preference"
            )
            evidence_list.append(evidence)

        if user_id not in self._evidence_buffer:
            self._evidence_buffer[user_id] = []
        self._evidence_buffer[user_id].extend(evidence_list)

    # ===== BATCH UPDATES =====

    async def apply_accumulated_evidence(
        self,
        user_id: str,
        min_evidence_count: int = 5
    ) -> Dict[str, Any]:
        """
        Apply accumulated evidence to update strengths

        Called periodically (e.g., daily) to update strengths based on
        accumulated behavioral evidence.

        Args:
            user_id: User to update
            min_evidence_count: Minimum evidence before updating

        Returns:
            Update summary
        """
        if user_id not in self._evidence_buffer:
            return {"updated": False, "reason": "no_evidence"}

        evidence_list = self._evidence_buffer[user_id]

        if len(evidence_list) < min_evidence_count:
            return {"updated": False, "reason": "insufficient_evidence", "count": len(evidence_list)}

        # Group evidence by strength type
        strength_adjustments: Dict[StrengthType, float] = {}
        strength_evidence_counts: Dict[StrengthType, int] = {}

        for evidence in evidence_list:
            if evidence.strength_type not in strength_adjustments:
                strength_adjustments[evidence.strength_type] = 0.0
                strength_evidence_counts[evidence.strength_type] = 0

            strength_adjustments[evidence.strength_type] += evidence.confidence_impact
            strength_evidence_counts[evidence.strength_type] += 1

        # Get or initialize user strengths
        if user_id not in self._user_strengths:
            self._user_strengths[user_id] = []

        updated_strengths = []

        for strength_type, adjustment in strength_adjustments.items():
            # Find existing strength or create new
            existing_strength = next(
                (s for s in self._user_strengths[user_id] if s.strength_type == strength_type),
                None
            )

            if existing_strength:
                # Update existing
                old_confidence = existing_strength.confidence_score
                new_confidence = max(0.0, min(1.0, old_confidence + adjustment))
                existing_strength.confidence_score = new_confidence

                updated_strengths.append({
                    "strength_type": strength_type.value,
                    "old_confidence": old_confidence,
                    "new_confidence": new_confidence,
                    "adjustment": adjustment,
                    "evidence_count": strength_evidence_counts[strength_type]
                })

                # Record in personality discovery module
                await self.discovery.update_strength_confidence(
                    user_id=user_id,
                    strength=existing_strength,
                    confidence_delta=adjustment,
                    reason=f"Accumulated {strength_evidence_counts[strength_type]} usage observations"
                )

            elif adjustment > 0.2:  # Only create new strength if strong signal
                # Create new strength
                from ..models import SignatureStrength

                new_strength = SignatureStrength(
                    strength_type=strength_type,
                    identity_label=self.discovery._get_identity_label(strength_type),
                    strength_description=self.discovery._get_strength_description(strength_type),
                    confidence_score=min(0.6, adjustment)  # Start conservative
                )

                self._user_strengths[user_id].append(new_strength)

                updated_strengths.append({
                    "strength_type": strength_type.value,
                    "old_confidence": 0.0,
                    "new_confidence": new_strength.confidence_score,
                    "adjustment": adjustment,
                    "evidence_count": strength_evidence_counts[strength_type],
                    "newly_discovered": True
                })

        # Clear evidence buffer
        self._evidence_buffer[user_id] = []

        return {
            "updated": True,
            "user_id": user_id,
            "total_evidence_processed": len(evidence_list),
            "strengths_updated": updated_strengths,
            "applied_at": datetime.utcnow().isoformat()
        }

    # ===== RETRIEVAL =====

    async def get_current_strengths(
        self,
        user_id: str,
        min_confidence: float = 0.3
    ) -> List[SignatureStrength]:
        """
        Get user's current strengths

        Args:
            user_id: User to get strengths for
            min_confidence: Minimum confidence threshold

        Returns:
            List of SignatureStrengths above threshold
        """
        if user_id not in self._user_strengths:
            return []

        return [
            s for s in self._user_strengths[user_id]
            if s.confidence_score >= min_confidence
        ]

    async def get_strength_trajectory(
        self,
        user_id: str,
        strength_type: StrengthType,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get trajectory of a strength over time

        Args:
            user_id: User to analyze
            strength_type: Which strength
            lookback_days: How far back to look

        Returns:
            Trajectory data
        """
        if user_id not in self._evidence_buffer:
            return {"strength_type": strength_type.value, "no_data": True}

        # Get evidence for this strength from last N days
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)

        relevant_evidence = [
            e for e in self._evidence_buffer.get(user_id, [])
            if e.strength_type == strength_type and e.observed_at >= cutoff
        ]

        if not relevant_evidence:
            return {"strength_type": strength_type.value, "no_recent_data": True}

        # Analyze trajectory
        positive_evidence = [e for e in relevant_evidence if e.confidence_impact > 0]
        negative_evidence = [e for e in relevant_evidence if e.confidence_impact < 0]

        total_impact = sum(e.confidence_impact for e in relevant_evidence)

        return {
            "strength_type": strength_type.value,
            "lookback_days": lookback_days,
            "total_evidence": len(relevant_evidence),
            "positive_evidence": len(positive_evidence),
            "negative_evidence": len(negative_evidence),
            "net_impact": total_impact,
            "trajectory": "growing" if total_impact > 0.1 else "stable" if total_impact > -0.1 else "declining"
        }

    # ===== INSIGHTS =====

    async def generate_insights(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate insights about user's evolving personality

        Args:
            user_id: User to generate insights for

        Returns:
            Insights dictionary
        """
        strengths = await self.get_current_strengths(user_id)

        if not strengths:
            return {"no_data": True}

        # Sort by confidence
        strengths.sort(key=lambda s: s.confidence_score, reverse=True)

        insights = {
            "top_strengths": [
                {
                    "type": s.strength_type.value,
                    "label": s.identity_label,
                    "confidence": s.confidence_score,
                    "examples": s.demonstrated_examples[-3:]  # Last 3 examples
                }
                for s in strengths[:3]
            ],
            "emerging_strengths": [
                {
                    "type": s.strength_type.value,
                    "label": s.identity_label,
                    "confidence": s.confidence_score
                }
                for s in strengths
                if 0.3 <= s.confidence_score < 0.6
            ],
            "total_strengths_identified": len(strengths)
        }

        return insights
