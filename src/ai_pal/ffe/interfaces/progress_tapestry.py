"""
Progress Tapestry - Visual Timeline of Earned Wins

NOT a to-do list! This is a celebration of what you've accomplished.
Each "thread" in the tapestry represents a completed atomic block,
woven together to show your growing competence and momentum.

Powered by:
- RewardEmitter (provides the wins to visualize)
- TimeBlockManager (provides atomic block structure)
- MomentumLoopOrchestrator (tracks cycle completions)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

from loguru import logger

from ..models import (
    AtomicBlock,
    RewardMessage,
    MomentumLoopState,
    StrengthType,
)


@dataclass
class TapestryView:
    """
    Visual representation of user's earned wins

    This is the data structure that powers the Progress Tapestry visualization.
    It's designed to show momentum, not pressure - a timeline of victories.
    """
    user_id: str
    period_start: datetime
    period_end: datetime

    # Core tapestry data
    completed_blocks: List[AtomicBlock] = field(default_factory=list)
    reward_messages: List[RewardMessage] = field(default_factory=list)
    momentum_cycles: List[MomentumLoopState] = field(default_factory=list)

    # Visualization metrics
    total_wins: int = 0
    total_blocks_completed: int = 0
    total_momentum_cycles: int = 0

    # Timeline data (for charting)
    wins_by_day: Dict[str, int] = field(default_factory=dict)  # ISO date -> win count
    pride_intensity_by_day: Dict[str, float] = field(default_factory=dict)  # ISO date -> avg intensity

    # Strength distribution (which strengths used most)
    strength_distribution: Dict[str, int] = field(default_factory=dict)  # strength_type -> count
    strongest_strength: Optional[str] = None

    # Pride tracking
    total_pride_hits: int = 0
    average_pride_intensity: float = 0.0
    pride_trend: List[float] = field(default_factory=list)  # Daily avg pride intensity

    # Time investment
    total_time_invested_minutes: int = 0
    average_block_duration_minutes: float = 0.0

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)


class ProgressTapestry:
    """
    Progress Tapestry - Visualization engine for earned wins

    This interface transforms completed blocks and rewards into a
    visual timeline that celebrates progress and builds momentum.

    Key principles:
    - Shows what you've DONE, not what you haven't
    - Visualizes momentum (streaks, cycles completed)
    - Highlights growth (new strengths used, bottlenecks overcome)
    - Pride-based (not shame-based) metrics
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize Progress Tapestry

        Args:
            storage_dir: Where to persist tapestry data
        """
        self.storage_dir = storage_dir or Path("./data/tapestry")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self.tapestries: Dict[str, TapestryView] = {}  # user_id -> latest tapestry

        logger.info(f"Progress Tapestry initialized with storage at {self.storage_dir}")

    async def render_tapestry(
        self,
        user_id: str,
        completed_blocks: List[AtomicBlock],
        rewards: List[RewardMessage],
        momentum_loops: List[MomentumLoopState],
        lookback_days: int = 30
    ) -> TapestryView:
        """
        Generate tapestry visualization data

        Args:
            user_id: User whose tapestry to render
            completed_blocks: All completed atomic blocks
            rewards: All rewards earned
            momentum_loops: All completed momentum loops
            lookback_days: How far back to include data

        Returns:
            TapestryView with visualization-ready data
        """
        logger.info(f"Rendering tapestry for user {user_id}, lookback={lookback_days} days")

        # Calculate period
        period_end = datetime.now()
        period_start = period_end - timedelta(days=lookback_days)

        # Filter to period
        blocks_in_period = [
            b for b in completed_blocks
            if b.completion_time and period_start <= b.completion_time <= period_end
        ]
        rewards_in_period = [
            r for r in rewards
            if r.emitted_at and period_start <= r.emitted_at <= period_end
        ]
        loops_in_period = [
            l for l in momentum_loops
            if l.started_at and period_start <= l.started_at <= period_end
        ]

        logger.debug(
            f"Period data: {len(blocks_in_period)} blocks, "
            f"{len(rewards_in_period)} rewards, "
            f"{len(loops_in_period)} loops"
        )

        # Create tapestry view
        tapestry = TapestryView(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            completed_blocks=blocks_in_period,
            reward_messages=rewards_in_period,
            momentum_cycles=loops_in_period,
        )

        # Calculate metrics
        tapestry.total_wins = len(blocks_in_period)
        tapestry.total_blocks_completed = len(blocks_in_period)
        tapestry.total_momentum_cycles = len(loops_in_period)

        # Timeline data (wins by day)
        tapestry.wins_by_day = await self._calculate_wins_by_day(blocks_in_period)

        # Strength distribution
        tapestry.strength_distribution = await self._calculate_strength_distribution(blocks_in_period)
        if tapestry.strength_distribution:
            tapestry.strongest_strength = max(
                tapestry.strength_distribution,
                key=tapestry.strength_distribution.get
            )

        # Pride metrics
        tapestry.total_pride_hits = len([r for r in rewards_in_period if r.reward_text])
        pride_intensities = [
            b.pride_hit_intensity for b in blocks_in_period
            if b.pride_hit_intensity > 0
        ]
        if pride_intensities:
            tapestry.average_pride_intensity = sum(pride_intensities) / len(pride_intensities)
            tapestry.pride_trend = pride_intensities  # Simplified - could be daily averages
        else:
            tapestry.average_pride_intensity = 0.0

        tapestry.pride_intensity_by_day = await self._calculate_pride_by_day(blocks_in_period)

        # Time investment
        time_minutes = [
            b.actual_duration_minutes for b in blocks_in_period
            if b.actual_duration_minutes
        ]
        if time_minutes:
            tapestry.total_time_invested_minutes = sum(time_minutes)
            tapestry.average_block_duration_minutes = sum(time_minutes) / len(time_minutes)
        else:
            tapestry.total_time_invested_minutes = 0
            tapestry.average_block_duration_minutes = 0.0

        # Cache tapestry
        self.tapestries[user_id] = tapestry

        # Persist to storage
        await self._save_tapestry(tapestry)

        logger.info(
            f"Tapestry rendered: {tapestry.total_wins} wins, "
            f"{tapestry.total_momentum_cycles} cycles, "
            f"avg pride: {tapestry.average_pride_intensity:.2f}"
        )

        return tapestry

    async def add_win_to_tapestry(
        self,
        user_id: str,
        block: AtomicBlock,
        reward: Optional[RewardMessage] = None
    ) -> None:
        """
        Add a new win to user's tapestry

        This is called when a block is completed to update the running tapestry.

        Args:
            user_id: User who completed the block
            block: Completed atomic block
            reward: Optional reward message
        """
        logger.debug(f"Adding win to tapestry for user {user_id}: block {block.block_id}")

        # Get or create tapestry
        if user_id in self.tapestries:
            tapestry = self.tapestries[user_id]
        else:
            # Create fresh tapestry
            tapestry = TapestryView(
                user_id=user_id,
                period_start=datetime.now() - timedelta(days=30),
                period_end=datetime.now()
            )
            self.tapestries[user_id] = tapestry

        # Add block
        tapestry.completed_blocks.append(block)
        tapestry.total_wins += 1
        tapestry.total_blocks_completed += 1

        # Add reward
        if reward:
            tapestry.reward_messages.append(reward)
            tapestry.total_pride_hits += 1

        # Update timestamp
        tapestry.generated_at = datetime.now()

        # Persist
        await self._save_tapestry(tapestry)

        logger.info(f"Win added to tapestry: total wins now {tapestry.total_wins}")

    async def get_tapestry_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for display

        Args:
            user_id: User to get stats for

        Returns:
            Dict of statistics
        """
        if user_id not in self.tapestries:
            logger.warning(f"No tapestry found for user {user_id}")
            return {
                "total_wins": 0,
                "total_momentum_cycles": 0,
                "strongest_strength": None,
                "average_pride_intensity": 0.0,
            }

        tapestry = self.tapestries[user_id]

        return {
            "total_wins": tapestry.total_wins,
            "total_blocks_completed": tapestry.total_blocks_completed,
            "total_momentum_cycles": tapestry.total_momentum_cycles,
            "strongest_strength": tapestry.strongest_strength,
            "average_pride_intensity": tapestry.average_pride_intensity,
            "total_pride_hits": tapestry.total_pride_hits,
            "total_time_invested_minutes": tapestry.total_time_invested_minutes,
            "average_block_duration_minutes": tapestry.average_block_duration_minutes,
        }

    async def get_streak_info(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate streak information (consecutive days with wins)

        Args:
            user_id: User to calculate streaks for

        Returns:
            Streak info dict
        """
        if user_id not in self.tapestries:
            return {"current_streak": 0, "longest_streak": 0}

        tapestry = self.tapestries[user_id]

        # Calculate current streak
        current_streak = 0
        today = datetime.now().date()
        check_date = today

        while True:
            date_str = check_date.isoformat()
            if tapestry.wins_by_day.get(date_str, 0) > 0:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        # Calculate longest streak (simple version - could be optimized)
        longest_streak = 0
        current_run = 0

        # Sort dates
        sorted_dates = sorted(tapestry.wins_by_day.keys())

        prev_date = None
        for date_str in sorted_dates:
            if tapestry.wins_by_day[date_str] > 0:
                date = datetime.fromisoformat(date_str).date()

                if prev_date and (date - prev_date).days == 1:
                    current_run += 1
                else:
                    current_run = 1

                longest_streak = max(longest_streak, current_run)
                prev_date = date

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
        }

    # ===== HELPER METHODS =====

    async def _calculate_wins_by_day(self, blocks: List[AtomicBlock]) -> Dict[str, int]:
        """Calculate number of wins per day"""
        wins_by_day = {}

        for block in blocks:
            if block.completion_time:
                date_str = block.completion_time.date().isoformat()
                wins_by_day[date_str] = wins_by_day.get(date_str, 0) + 1

        return wins_by_day

    async def _calculate_pride_by_day(self, blocks: List[AtomicBlock]) -> Dict[str, float]:
        """Calculate average pride intensity per day"""
        pride_by_day = {}
        count_by_day = {}

        for block in blocks:
            if block.completion_time and block.pride_hit_intensity > 0:
                date_str = block.completion_time.date().isoformat()
                pride_by_day[date_str] = pride_by_day.get(date_str, 0.0) + block.pride_hit_intensity
                count_by_day[date_str] = count_by_day.get(date_str, 0) + 1

        # Calculate averages
        for date_str in pride_by_day:
            pride_by_day[date_str] /= count_by_day[date_str]

        return pride_by_day

    async def _calculate_strength_distribution(self, blocks: List[AtomicBlock]) -> Dict[str, int]:
        """Calculate which strengths were used most"""
        distribution = {}

        for block in blocks:
            if block.using_strength:
                strength_name = block.using_strength.value if isinstance(block.using_strength, StrengthType) else str(block.using_strength)
                distribution[strength_name] = distribution.get(strength_name, 0) + 1

        return distribution

    async def _save_tapestry(self, tapestry: TapestryView) -> None:
        """Persist tapestry to storage"""
        try:
            file_path = self.storage_dir / f"{tapestry.user_id}_tapestry.json"

            # Convert to dict (simplified - would need full serialization)
            data = {
                "user_id": tapestry.user_id,
                "period_start": tapestry.period_start.isoformat(),
                "period_end": tapestry.period_end.isoformat(),
                "total_wins": tapestry.total_wins,
                "total_blocks_completed": tapestry.total_blocks_completed,
                "total_momentum_cycles": tapestry.total_momentum_cycles,
                "wins_by_day": tapestry.wins_by_day,
                "pride_intensity_by_day": tapestry.pride_intensity_by_day,
                "strength_distribution": tapestry.strength_distribution,
                "strongest_strength": tapestry.strongest_strength,
                "total_pride_hits": tapestry.total_pride_hits,
                "average_pride_intensity": tapestry.average_pride_intensity,
                "total_time_invested_minutes": tapestry.total_time_invested_minutes,
                "average_block_duration_minutes": tapestry.average_block_duration_minutes,
                "generated_at": tapestry.generated_at.isoformat(),
            }

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Tapestry saved to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save tapestry: {e}")

    async def _load_tapestry(self, user_id: str) -> Optional[TapestryView]:
        """Load tapestry from storage"""
        try:
            file_path = self.storage_dir / f"{user_id}_tapestry.json"

            if not file_path.exists():
                return None

            with open(file_path, 'r') as f:
                data = json.load(f)

            # Create tapestry (simplified - would need full deserialization)
            tapestry = TapestryView(
                user_id=data["user_id"],
                period_start=datetime.fromisoformat(data["period_start"]),
                period_end=datetime.fromisoformat(data["period_end"]),
                total_wins=data["total_wins"],
                total_blocks_completed=data["total_blocks_completed"],
                total_momentum_cycles=data["total_momentum_cycles"],
                wins_by_day=data["wins_by_day"],
                pride_intensity_by_day=data["pride_intensity_by_day"],
                strength_distribution=data["strength_distribution"],
                strongest_strength=data.get("strongest_strength"),
                total_pride_hits=data["total_pride_hits"],
                average_pride_intensity=data["average_pride_intensity"],
                total_time_invested_minutes=data["total_time_invested_minutes"],
                average_block_duration_minutes=data["average_block_duration_minutes"],
                generated_at=datetime.fromisoformat(data["generated_at"]),
            )

            logger.debug(f"Tapestry loaded from {file_path}")
            return tapestry

        except Exception as e:
            logger.error(f"Failed to load tapestry: {e}")
            return None
