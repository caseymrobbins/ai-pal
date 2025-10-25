"""
Epic Meaning Module - Connect atomic wins to core values and life goals

This module provides the "why" behind the work. It transforms
task completion from mere productivity into meaningful progress
toward the user's life vision.

Powered by:
- GoalIngestor (defines the quest)
- PersonalityModule (provides user's core values)

Integrates with:
- Narrative Arc Interface (displays epic meaning)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from loguru import logger

from ..models import (
    AtomicBlock,
    PersonalityProfile,
    MeaningNarrative,
)


@dataclass
class NarrativeArc:
    """
    Epic narrative connecting wins to values

    This is the data structure for the Narrative Arc Engine.
    It shows how small daily wins contribute to big-picture goals.
    """
    user_id: str
    core_value: str  # e.g., "Community"
    life_goal: str   # e.g., "Build app for community"

    # Connected wins
    contributing_blocks: List[AtomicBlock] = field(default_factory=list)
    narrative_text: str = ""  # Generated story

    # Progress tracking
    progress_toward_goal: float = 0.0  # 0-1 scale
    meaning_intensity: float = 0.0     # 0-1 scale
    milestones_reached: List[str] = field(default_factory=list)

    # Metadata
    arc_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


class EpicMeaningModule:
    """
    Epic Meaning Module - Narrative Arc Engine backend

    Connects atomic task completions to user's core values
    and life goals, providing a sense of purpose and progress.

    Key principles:
    - Makes work meaningful (not just productive)
    - Shows long-term progress (not just daily tasks)
    - Connects to identity (not external validation)
    - Celebrates milestones (not just completion)
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize Epic Meaning Module

        Args:
            storage_dir: Where to persist narrative arcs
        """
        self.storage_dir = storage_dir or Path("./data/epic_meaning")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self.narrative_arcs: Dict[str, List[NarrativeArc]] = {}  # user_id -> arcs

        # Simple narrative templates
        self.narrative_templates = {
            "early_progress": "You've taken your first steps toward {goal}. Each {value}-aligned action builds the foundation.",
            "quarter_progress": "You're making real progress on {goal}. Your {value} is shining through in every task.",
            "half_progress": "You're halfway there! Your commitment to {value} through {goal} is impressive.",
            "final_stretch": "The finish line is in sight for {goal}. Your {value} has guided you this far.",
            "milestone": "Milestone reached! This {value}-driven work on {goal} is creating real impact.",
        }

        logger.info(f"Epic Meaning Module initialized with storage at {self.storage_dir}")

    async def generate_narrative(
        self,
        user_id: str,
        block: AtomicBlock,
        personality: PersonalityProfile
    ) -> MeaningNarrative:
        """
        Generate epic meaning connection for completed block

        Links the atomic win to the user's core values and life goals.

        Args:
            user_id: User who completed the block
            block: Completed atomic block
            personality: User's personality profile

        Returns:
            MeaningNarrative connecting block to values/goals
        """
        logger.info(f"Generating narrative for user {user_id}, block {block.block_id}")

        # Find best matching value and goal
        best_value = await self._find_matching_value(block, personality.core_values)
        best_goal = await self._find_matching_goal(block, personality.life_goals)

        if not best_value or not best_goal:
            logger.warning("Could not find matching value/goal for narrative")
            # Create generic narrative
            return MeaningNarrative(
                user_id=user_id,
                block_id=block.block_id,
                linked_core_value="Growth",
                linked_life_goal="Personal development",
                connection_narrative="This task contributes to your growth journey.",
                meaning_intensity=0.5,
            )

        # Generate connection narrative
        narrative_text = await self._generate_connection_text(
            block.description,
            best_value,
            best_goal
        )

        # Calculate meaning intensity
        meaning_intensity = await self._calculate_meaning_intensity(
            block,
            best_value,
            best_goal
        )

        # Create meaning narrative
        narrative = MeaningNarrative(
            user_id=user_id,
            block_id=block.block_id,
            linked_core_value=best_value,
            linked_life_goal=best_goal,
            connection_narrative=narrative_text,
            meaning_intensity=meaning_intensity,
            long_term_vision_reminder=True,
        )

        logger.info(
            f"Narrative generated: '{narrative_text[:50]}...' "
            f"(intensity: {meaning_intensity:.2f})"
        )

        return narrative

    async def show_quest_progress(
        self,
        user_id: str,
        life_goal: str,
        completed_blocks: List[AtomicBlock]
    ) -> NarrativeArc:
        """
        Display progress toward big-picture goal

        Creates or updates narrative arc showing the user's quest.

        Args:
            user_id: User to show progress for
            life_goal: Life goal to track
            completed_blocks: All blocks related to this goal

        Returns:
            NarrativeArc showing epic progress
        """
        logger.info(f"Showing quest progress for user {user_id}: '{life_goal}'")

        # Find or create arc
        arc = await self._find_or_create_arc(user_id, life_goal)

        # Update with new blocks
        arc.contributing_blocks = [
            b for b in completed_blocks
            if await self._block_contributes_to_goal(b, life_goal)
        ]

        # Calculate progress
        # Simple heuristic: progress based on number of blocks completed
        # In full version, would use more sophisticated estimation
        total_blocks = len(arc.contributing_blocks)
        if total_blocks == 0:
            arc.progress_toward_goal = 0.0
        elif total_blocks < 5:
            arc.progress_toward_goal = 0.1  # Early progress
        elif total_blocks < 10:
            arc.progress_toward_goal = 0.25  # Quarter progress
        elif total_blocks < 20:
            arc.progress_toward_goal = 0.5  # Halfway
        elif total_blocks < 30:
            arc.progress_toward_goal = 0.75  # Final stretch
        else:
            arc.progress_toward_goal = 0.9  # Near completion

        # Generate narrative based on progress
        arc.narrative_text = await self._generate_arc_narrative(arc)

        # Update metadata
        arc.last_updated = datetime.now()

        # Save arc
        await self._save_arc(arc)

        logger.info(
            f"Quest progress: {arc.progress_toward_goal:.0%} "
            f"({len(arc.contributing_blocks)} blocks completed)"
        )

        return arc

    async def link_block_to_value(
        self,
        block: AtomicBlock,
        value: str
    ) -> str:
        """
        Create narrative linking atomic win to core value

        Args:
            block: Completed block
            value: Core value to link to

        Returns:
            Narrative text
        """
        logger.debug(f"Linking block {block.block_id} to value '{value}'")

        # Simple template-based narrative
        narratives = [
            f"By completing '{block.title}', you honored your value of {value}.",
            f"This work on '{block.title}' reflects your commitment to {value}.",
            f"'{block.title}' is a concrete expression of your {value} value.",
        ]

        # Choose based on block ID for variety
        index = hash(block.block_id) % len(narratives)
        narrative = narratives[index]

        return narrative

    # ===== HELPER METHODS =====

    async def _find_matching_value(
        self,
        block: AtomicBlock,
        values: List[str]
    ) -> Optional[str]:
        """Find best matching core value for a block"""
        if not values:
            return None

        # Simple keyword matching (could be enhanced with NLP)
        block_text = (block.description + " " + block.title).lower()

        for value in values:
            if value.lower() in block_text:
                return value

        # Default to first value
        return values[0]

    async def _find_matching_goal(
        self,
        block: AtomicBlock,
        goals: List[str]
    ) -> Optional[str]:
        """Find best matching life goal for a block"""
        if not goals:
            return None

        # Simple keyword matching
        block_text = (block.description + " " + block.title).lower()

        for goal in goals:
            goal_keywords = goal.lower().split()
            if any(keyword in block_text for keyword in goal_keywords):
                return goal

        # Default to first goal
        return goals[0]

    async def _generate_connection_text(
        self,
        task_description: str,
        value: str,
        goal: str
    ) -> str:
        """Generate narrative connecting task to value and goal"""
        narratives = [
            f"This work on '{task_description}' brings you closer to {goal}, guided by your value of {value}.",
            f"By focusing on {value} through this task, you're building toward {goal}.",
            f"Each step toward {goal} reflects your commitment to {value}. This task is part of that journey.",
        ]

        # Simple selection
        return narratives[0]

    async def _calculate_meaning_intensity(
        self,
        block: AtomicBlock,
        value: str,
        goal: str
    ) -> float:
        """Calculate how meaningful this connection is"""
        # Simple heuristic - could be enhanced
        intensity = 0.5  # Base

        # Bonus for strong connection indicators
        block_text = (block.description + " " + block.title).lower()

        if value.lower() in block_text:
            intensity += 0.2

        if any(keyword.lower() in block_text for keyword in goal.split()):
            intensity += 0.2

        # Bonus for high quality work
        if block.quality_score > 0.8:
            intensity += 0.1

        return min(1.0, intensity)

    async def _find_or_create_arc(
        self,
        user_id: str,
        life_goal: str
    ) -> NarrativeArc:
        """Find existing arc or create new one"""
        # Check cache
        if user_id in self.narrative_arcs:
            for arc in self.narrative_arcs[user_id]:
                if arc.life_goal == life_goal:
                    return arc

        # Create new arc
        arc = NarrativeArc(
            user_id=user_id,
            core_value="Growth",  # Default - would be inferred from personality
            life_goal=life_goal,
            arc_id=f"{user_id}_{hash(life_goal)}",
        )

        # Cache it
        if user_id not in self.narrative_arcs:
            self.narrative_arcs[user_id] = []
        self.narrative_arcs[user_id].append(arc)

        return arc

    async def _block_contributes_to_goal(
        self,
        block: AtomicBlock,
        goal: str
    ) -> bool:
        """Check if block contributes to goal"""
        # Simple keyword matching
        block_text = (block.description + " " + block.title).lower()
        goal_keywords = goal.lower().split()

        return any(keyword in block_text for keyword in goal_keywords)

    async def _generate_arc_narrative(self, arc: NarrativeArc) -> str:
        """Generate narrative for entire arc based on progress"""
        progress = arc.progress_toward_goal

        if progress < 0.2:
            template = self.narrative_templates["early_progress"]
        elif progress < 0.4:
            template = self.narrative_templates["quarter_progress"]
        elif progress < 0.6:
            template = self.narrative_templates["half_progress"]
        elif progress < 0.8:
            template = self.narrative_templates["final_stretch"]
        else:
            template = self.narrative_templates["milestone"]

        narrative = template.format(
            goal=arc.life_goal,
            value=arc.core_value
        )

        return narrative

    async def _save_arc(self, arc: NarrativeArc) -> None:
        """Persist narrative arc"""
        try:
            file_path = self.storage_dir / f"{arc.arc_id}.json"

            data = {
                "user_id": arc.user_id,
                "arc_id": arc.arc_id,
                "core_value": arc.core_value,
                "life_goal": arc.life_goal,
                "narrative_text": arc.narrative_text,
                "progress_toward_goal": arc.progress_toward_goal,
                "meaning_intensity": arc.meaning_intensity,
                "contributing_blocks_count": len(arc.contributing_blocks),
                "created_at": arc.created_at.isoformat(),
                "last_updated": arc.last_updated.isoformat(),
            }

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Narrative arc saved to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save narrative arc: {e}")
