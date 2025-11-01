"""
Growth Scaffold Component (Basic MVP Version)

The "subtle helper" - passively detects avoided tasks and queues them
for strength-based reframing during momentum loops.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from loguru import logger

from ..component_interfaces import IGrowthScaffold
from ..models import BottleneckTask, BottleneckReason, SignatureStrength


class GrowthScaffold(IGrowthScaffold):
    """
    Basic implementation of Growth Scaffold

    Detects bottleneck tasks and queues them for reframing.
    Full ARI integration will be implemented in Phase 5.2.
    """

    def __init__(self):
        """Initialize Growth Scaffold"""
        self.detected_bottlenecks = {}  # bottleneck_id -> BottleneckTask
        self.bottleneck_queue = []  # List of bottleneck_ids to reframe
        logger.info("Growth Scaffold initialized (basic MVP version)")

    async def detect_bottlenecks(
        self,
        user_id: str,
        lookback_days: int = 30
    ) -> List[BottleneckTask]:
        """
        Detect tasks the user avoids or struggles with

        Basic version: returns previously identified bottlenecks.
        Full version will integrate with ARI Monitor for pattern detection.

        Args:
            user_id: User to analyze
            lookback_days: How far back to look

        Returns:
            List of detected bottleneck tasks
        """
        logger.debug(f"Detecting bottlenecks for user {user_id} (last {lookback_days} days)")

        # Get user's bottlenecks
        user_bottlenecks = [
            b for b in self.detected_bottlenecks.values()
            if b.user_id == user_id
        ]

        # Filter to recent ones
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        recent_bottlenecks = [
            b for b in user_bottlenecks
            if b.detected_at >= cutoff_date
        ]

        logger.info(f"Found {len(recent_bottlenecks)} bottlenecks for user {user_id}")

        return recent_bottlenecks

    async def queue_bottleneck(
        self,
        bottleneck: BottleneckTask
    ) -> None:
        """
        Queue a bottleneck task for future reframing

        Bottleneck will be activated when next pride hit occurs.

        Args:
            bottleneck: Bottleneck to queue
        """
        logger.info(f"Queueing bottleneck {bottleneck.bottleneck_id}: '{bottleneck.task_description[:50]}...'")

        # Store bottleneck
        self.detected_bottlenecks[bottleneck.bottleneck_id] = bottleneck

        # Add to queue if not already there
        if bottleneck.bottleneck_id not in self.bottleneck_queue:
            self.bottleneck_queue.append(bottleneck.bottleneck_id)

        logger.debug(f"Bottleneck queue size: {len(self.bottleneck_queue)}")

    async def get_next_bottleneck(self, user_id: str) -> Optional[BottleneckTask]:
        """
        Get next bottleneck for reframing

        Args:
            user_id: User to get bottleneck for

        Returns:
            Next BottleneckTask or None
        """
        # Find first queued bottleneck for this user
        for bottleneck_id in self.bottleneck_queue:
            bottleneck = self.detected_bottlenecks.get(bottleneck_id)
            if bottleneck and bottleneck.user_id == user_id:
                logger.info(f"Retrieved bottleneck {bottleneck_id} for user {user_id}")
                return bottleneck

        logger.debug(f"No queued bottlenecks for user {user_id}")
        return None

    async def mark_bottleneck_reframed(self, bottleneck_id: str) -> None:
        """
        Mark a bottleneck as successfully reframed

        Args:
            bottleneck_id: ID of bottleneck that was reframed
        """
        if bottleneck_id in self.bottleneck_queue:
            self.bottleneck_queue.remove(bottleneck_id)
            logger.info(f"Marked bottleneck {bottleneck_id} as reframed, removed from queue")

        # Update bottleneck record
        if bottleneck_id in self.detected_bottlenecks:
            bottleneck = self.detected_bottlenecks[bottleneck_id]
            bottleneck.reframed = True
            bottleneck.reframed_at = datetime.now()

    async def report_avoidance(
        self,
        user_id: str,
        task_description: str,
        reason: BottleneckReason
    ) -> BottleneckTask:
        """
        Report a task that user is avoiding

        Args:
            user_id: User avoiding the task
            task_description: What task is being avoided
            reason: Why it's a bottleneck

        Returns:
            Created BottleneckTask
        """
        logger.info(f"Reporting avoidance for user {user_id}: '{task_description[:50]}...'")

        bottleneck = BottleneckTask(
            bottleneck_id=str(uuid.uuid4()),
            user_id=user_id,
            task_description=task_description,
            task_category="",  # Could be inferred later
            bottleneck_reason=reason,
            detection_method="user_report",
            avoidance_count=1,
            last_avoided=datetime.now(),
            queued=True,
            queued_date=datetime.now(),
        )

        # Queue it
        await self.queue_bottleneck(bottleneck)

        return bottleneck

    def get_bottleneck_count(self, user_id: str) -> int:
        """Get total number of bottlenecks for user"""
        return len([b for b in self.detected_bottlenecks.values() if b.user_id == user_id])

    async def get_queued_bottleneck(
        self,
        user_id: str,
        strength: Optional[SignatureStrength] = None
    ) -> Optional[BottleneckTask]:
        """Get the next bottleneck from queue (wraps get_next_bottleneck)"""
        return await self.get_next_bottleneck(user_id)

    async def activate_bottleneck_on_pride_hit(
        self,
        user_id: str,
        pride_hit_intensity: float
    ) -> Optional[BottleneckTask]:
        """Trigger bottleneck activation when pride hit occurs"""
        # In MVP, just return next bottleneck if pride hit is strong enough
        if pride_hit_intensity > 0.7:
            return await self.get_next_bottleneck(user_id)
        return None
