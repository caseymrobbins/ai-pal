"""
Curiosity Compass - Exploration Opportunity Discovery

Turns the Growth Scaffold's bottleneck queue into a "map of curiosities".
Reframes avoided/difficult tasks as low-stakes exploration opportunities.

Instead of:
  "You should do this task you've been avoiding"

Shows:
  "What if we just explored this for 15 minutes? No pressure, just curiosity."

Powered by:
- GrowthScaffold (bottleneck queue)
- ScopingAgent (creates 15-minute explorations)
- StrengthAmplifier (reframes via curiosity/strengths)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from ..models import (
    BottleneckTask,
    BottleneckReason,
    AtomicBlock,
    SignatureStrength,
    TimeBlockSize,
)


@dataclass
class CuriosityMap:
    """
    Map of exploration opportunities

    Visualizes bottlenecks as curiosities to explore, not tasks to complete.
    """
    user_id: str

    # Opportunities (bottlenecks reframed as explorations)
    unexplored_areas: List[BottleneckTask] = field(default_factory=list)
    exploration_suggestions: List[Dict[str, Any]] = field(default_factory=list)

    # Low-stakes framing
    fifteen_min_explorations: List[AtomicBlock] = field(default_factory=list)

    # Discovery tracking
    explored_count: int = 0
    discoveries_made: List[str] = field(default_factory=list)

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExplorationOpportunity:
    """
    A single exploration opportunity

    Low-stakes, curiosity-driven approach to a bottleneck.
    """
    opportunity_id: str
    bottleneck_id: str
    user_id: str

    # Original bottleneck
    avoided_task: str
    avoidance_reason: BottleneckReason

    # Reframed as exploration
    exploration_prompt: str  # Curiosity-driven framing
    exploration_block: AtomicBlock  # 15-minute exploration

    # Discovery potential
    what_you_might_discover: List[str] = field(default_factory=list)
    why_this_is_interesting: str = ""

    # Safety/reassurance
    no_commitment_message: str = "Just 15 minutes to explore. No pressure to continue."
    escape_hatch: str = "You can stop anytime if it's not interesting."


class CuriosityCompass:
    """
    Curiosity Compass - Exploration opportunity discovery interface

    Transforms avoided tasks into curiosity-driven explorations.

    Key principles:
    - Low-stakes (just 15 minutes)
    - Curiosity-driven (not obligation-driven)
    - Discovery-focused (what might you learn?)
    - No pressure (escape hatch always available)
    - Pride-based (celebrate discoveries, not completion)
    """

    def __init__(self, growth_scaffold, scoping_agent, strength_amplifier):
        """
        Initialize Curiosity Compass

        Args:
            growth_scaffold: GrowthScaffold instance
            scoping_agent: ScopingAgent instance
            strength_amplifier: StrengthAmplifier instance
        """
        self.growth_scaffold = growth_scaffold
        self.scoping_agent = scoping_agent
        self.strength_amplifier = strength_amplifier

        # Curiosity templates for reframing
        self.curiosity_frames = {
            BottleneckReason.AVOIDED: [
                "What if we just peeked at {task}? No commitment, just curiosity.",
                "I wonder what {task} is actually like? Let's explore for 15 minutes.",
                "Curious what you'd discover if you tried {task} with no pressure?",
            ],
            BottleneckReason.DIFFICULT: [
                "What makes {task} tricky? Let's investigate for 15 minutes.",
                "I'm curious - what's the interesting puzzle in {task}?",
                "Let's explore why {task} feels hard. Might be fascinating!",
            ],
            BottleneckReason.BORING: [
                "What if there's something interesting hiding in {task}? Let's find out.",
                "Curious if we can find the interesting angle in {task}?",
                "Let's see if {task} is actually boring, or just seems that way.",
            ],
            BottleneckReason.ANXIETY_INDUCING: [
                "What if we just looked at {task} from a distance? No pressure.",
                "Curious what {task} looks like when there's no stakes? Let's explore.",
                "Let's investigate {task} in a totally safe, low-pressure way.",
            ],
            BottleneckReason.SKILL_GAP: [
                "What would you learn from exploring {task} for 15 minutes?",
                "Curious what skill you'd pick up from just trying {task}?",
                "Let's discover what {task} teaches you. No perfection needed.",
            ],
            BottleneckReason.UNCLEAR: [
                "What's actually going on with {task}? Let's investigate!",
                "I'm curious what {task} really involves. Want to explore?",
                "Let's uncover what {task} is actually about. Mystery solved!",
            ],
        }

        logger.info("Curiosity Compass initialized")

    async def show_curiosity_map(
        self,
        user_id: str
    ) -> CuriosityMap:
        """
        Display map of unexplored opportunities

        Args:
            user_id: User to show map for

        Returns:
            CuriosityMap with exploration opportunities
        """
        logger.info(f"Showing curiosity map for user {user_id}")

        # Get bottlenecks from growth scaffold
        bottlenecks = await self.growth_scaffold.detect_bottlenecks(
            user_id=user_id,
            lookback_days=90  # Wide window for curiosity
        )

        # Create map
        curiosity_map = CuriosityMap(
            user_id=user_id,
            unexplored_areas=bottlenecks,
        )

        # Generate exploration suggestions
        for bottleneck in bottlenecks[:5]:  # Top 5 opportunities
            suggestion = await self._create_exploration_suggestion(bottleneck)
            curiosity_map.exploration_suggestions.append(suggestion)

        # Count discoveries
        # (In full version, would track what user actually discovered)
        curiosity_map.explored_count = 0
        curiosity_map.discoveries_made = []

        logger.info(
            f"Curiosity map generated: {len(curiosity_map.unexplored_areas)} areas, "
            f"{len(curiosity_map.exploration_suggestions)} suggestions"
        )

        return curiosity_map

    async def suggest_exploration(
        self,
        user_id: str,
        strength: Optional[SignatureStrength] = None
    ) -> ExplorationOpportunity:
        """
        Suggest low-stakes 15-minute exploration

        Args:
            user_id: User to suggest exploration for
            strength: Optional strength to use for reframing

        Returns:
            ExplorationOpportunity
        """
        logger.info(f"Suggesting exploration for user {user_id}")

        # Get next bottleneck
        bottleneck = await self.growth_scaffold.get_next_bottleneck(user_id)
        if not bottleneck:
            logger.info("No bottlenecks available for exploration")
            return None

        # Create exploration opportunity
        opportunity = await self._create_exploration_opportunity(
            bottleneck=bottleneck,
            strength=strength
        )

        logger.info(
            f"Exploration opportunity created: '{opportunity.exploration_prompt}'"
        )

        return opportunity

    async def record_discovery(
        self,
        user_id: str,
        bottleneck_id: str,
        discovery: str,
        wants_to_continue: bool = False
    ) -> Dict[str, Any]:
        """
        Record what user discovered during exploration

        Args:
            user_id: User who explored
            bottleneck_id: Bottleneck that was explored
            discovery: What user discovered
            wants_to_continue: Does user want to continue exploring?

        Returns:
            Discovery celebration
        """
        logger.info(
            f"Recording discovery for user {user_id}: '{discovery}' "
            f"(continue: {wants_to_continue})"
        )

        # Celebrate discovery (not completion!)
        celebration = {
            "discovery": discovery,
            "celebration_message": await self._celebrate_discovery(discovery),
            "wants_more": wants_to_continue,
        }

        if wants_to_continue:
            celebration["next_exploration"] = await self.suggest_exploration(user_id)
        else:
            celebration["next_exploration"] = None
            celebration["closure_message"] = "Great exploration! You can come back to this anytime."

        logger.info(f"Discovery celebrated: {celebration['celebration_message']}")

        return celebration

    async def get_discovery_log(
        self,
        user_id: str,
        lookback_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Show user's discovery history

        Args:
            user_id: User to show log for
            lookback_days: How far back to look

        Returns:
            List of discoveries
        """
        logger.info(f"Getting discovery log for user {user_id}")

        # In full version, would retrieve from storage
        # For now, return structure
        discoveries = []

        return discoveries

    # ===== HELPER METHODS =====

    async def _create_exploration_suggestion(
        self,
        bottleneck: BottleneckTask
    ) -> Dict[str, Any]:
        """Create exploration suggestion from bottleneck"""
        # Reframe using curiosity template
        templates = self.curiosity_frames.get(
            bottleneck.bottleneck_reason,
            self.curiosity_frames[BottleneckReason.UNCLEAR]
        )

        curiosity_prompt = templates[0].format(task=bottleneck.task_description)

        suggestion = {
            "bottleneck_id": bottleneck.bottleneck_id,
            "task": bottleneck.task_description,
            "reason": bottleneck.bottleneck_reason.value,
            "curiosity_prompt": curiosity_prompt,
            "duration": "15 minutes",
            "commitment_level": "None - just exploring",
        }

        return suggestion

    async def _create_exploration_opportunity(
        self,
        bottleneck: BottleneckTask,
        strength: Optional[SignatureStrength] = None
    ) -> ExplorationOpportunity:
        """Create full exploration opportunity"""
        # Generate curiosity prompt
        templates = self.curiosity_frames.get(
            bottleneck.bottleneck_reason,
            self.curiosity_frames[BottleneckReason.UNCLEAR]
        )
        exploration_prompt = templates[0].format(task=bottleneck.task_description)

        # Create 15-minute exploration block
        exploration_block = AtomicBlock(
            user_id=bottleneck.user_id,
            goal_id=bottleneck.bottleneck_id,
            title=f"Explore: {bottleneck.task_description[:50]}",
            description=exploration_prompt,
            time_block_size=TimeBlockSize.SPRINT_15,  # Always 15 minutes
            original_description=bottleneck.task_description,
        )

        # Reframe via strength if provided
        if strength:
            reframed = await self.strength_amplifier.reframe_task_via_strength(
                exploration_block.description,
                strength
            )
            exploration_block.strength_reframe = reframed
            exploration_block.using_strength = strength.strength_type

        # Generate discovery potential
        discoveries = await self._generate_discovery_potential(bottleneck)

        # Create opportunity
        opportunity = ExplorationOpportunity(
            opportunity_id=f"explore_{bottleneck.bottleneck_id}",
            bottleneck_id=bottleneck.bottleneck_id,
            user_id=bottleneck.user_id,
            avoided_task=bottleneck.task_description,
            avoidance_reason=bottleneck.bottleneck_reason,
            exploration_prompt=exploration_prompt,
            exploration_block=exploration_block,
            what_you_might_discover=discoveries,
            why_this_is_interesting=await self._explain_why_interesting(bottleneck),
        )

        return opportunity

    async def _generate_discovery_potential(
        self,
        bottleneck: BottleneckTask
    ) -> List[str]:
        """Generate what user might discover"""
        # Simple template-based (would be AI-powered in full version)
        discoveries = [
            f"How {bottleneck.task_description} actually works",
            f"Why people find {bottleneck.task_description} valuable",
            f"A new angle on {bottleneck.task_description} you hadn't considered",
        ]
        return discoveries

    async def _explain_why_interesting(
        self,
        bottleneck: BottleneckTask
    ) -> str:
        """Explain why this exploration is interesting"""
        reason_explanations = {
            BottleneckReason.AVOIDED: "Sometimes the things we avoid are exactly what we need to explore.",
            BottleneckReason.DIFFICULT: "The hard problems are often the most interesting puzzles.",
            BottleneckReason.BORING: "What seems boring at first often has hidden depth.",
            BottleneckReason.ANXIETY_INDUCING: "Exploring safely can transform anxiety into curiosity.",
            BottleneckReason.SKILL_GAP: "The fastest way to learn is through curious exploration.",
            BottleneckReason.UNCLEAR: "Mystery is the beginning of discovery.",
        }

        return reason_explanations.get(
            bottleneck.bottleneck_reason,
            "Every exploration teaches us something new."
        )

    async def _celebrate_discovery(self, discovery: str) -> str:
        """Generate celebration for discovery"""
        celebrations = [
            f"Fascinating discovery! You learned: {discovery}",
            f"Great exploration! You uncovered: {discovery}",
            f"Excellent detective work! You discovered: {discovery}",
        ]
        return celebrations[0]
