"""
Cache Invalidation Strategies

Defines TTL-based and event-based cache invalidation patterns.
"""

from enum import Enum
from typing import List, Optional
from dataclasses import dataclass


class CacheTTL(Enum):
    """Cache TTL configuration for different data types"""

    # Hot data (frequently updated)
    SYSTEM_HEALTH = 60  # 1 minute
    AUDIT_LOGS = 60  # 1 minute
    TASK_STATUS = 120  # 2 minutes
    DASHBOARD_METRICS = 300  # 5 minutes

    # Warm data (regularly updated)
    ARI_METRICS = 300  # 5 minutes
    ARI_HISTORY = 600  # 10 minutes
    GOAL_DETAILS = 600  # 10 minutes
    GOAL_PREDICTIONS = 900  # 15 minutes

    # Cold data (infrequently updated)
    USER_PROFILE = 1800  # 30 minutes
    SYSTEM_CONFIG = 3600  # 1 hour


class CacheEvent(Enum):
    """Cache invalidation events"""

    # User events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"

    # ARI events
    ARI_SNAPSHOT_CREATED = "ari_snapshot_created"
    ARI_TREND_ANALYSIS = "ari_trend_analysis"

    # Goal events
    GOAL_CREATED = "goal_created"
    GOAL_UPDATED = "goal_updated"
    GOAL_COMPLETED = "goal_completed"

    # Task events
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # Prediction events
    PREDICTION_GENERATED = "prediction_generated"

    # System events
    HEALTH_DEGRADED = "health_degraded"
    HEALTH_RECOVERED = "health_recovered"


@dataclass
class CacheInvalidationRule:
    """Defines what cache keys to invalidate on an event"""

    event: CacheEvent
    patterns: List[str]  # Key patterns to invalidate (e.g., "user:ari:*:{user_id}")

    def __post_init__(self):
        """Validate patterns"""
        if not self.patterns:
            raise ValueError("At least one pattern required")


# ============================================================================
# Cache Invalidation Rules
# ============================================================================

INVALIDATION_RULES = {
    CacheEvent.ARI_SNAPSHOT_CREATED: CacheInvalidationRule(
        event=CacheEvent.ARI_SNAPSHOT_CREATED,
        patterns=[
            "user:ari:latest:{user_id}",
            "user:ari:history:{user_id}:*",
            "dashboard:metrics:{user_id}",
        ]
    ),

    CacheEvent.GOAL_CREATED: CacheInvalidationRule(
        event=CacheEvent.GOAL_CREATED,
        patterns=[
            "user:goals:active:{user_id}",
            "dashboard:metrics:{user_id}",
        ]
    ),

    CacheEvent.GOAL_UPDATED: CacheInvalidationRule(
        event=CacheEvent.GOAL_UPDATED,
        patterns=[
            "goal:{goal_id}",
            "user:goals:active:{user_id}",
            "goal:prediction:{goal_id}",
            "dashboard:metrics:{user_id}",
        ]
    ),

    CacheEvent.GOAL_COMPLETED: CacheInvalidationRule(
        event=CacheEvent.GOAL_COMPLETED,
        patterns=[
            "goal:{goal_id}",
            "user:goals:active:{user_id}",
            "dashboard:metrics:{user_id}",
        ]
    ),

    CacheEvent.TASK_COMPLETED: CacheInvalidationRule(
        event=CacheEvent.TASK_COMPLETED,
        patterns=[
            "user:tasks:{user_id}:*",
            "dashboard:metrics:{user_id}",
        ]
    ),

    CacheEvent.TASK_FAILED: CacheInvalidationRule(
        event=CacheEvent.TASK_FAILED,
        patterns=[
            "user:tasks:{user_id}:*",
            "dashboard:metrics:{user_id}",
        ]
    ),

    CacheEvent.USER_UPDATED: CacheInvalidationRule(
        event=CacheEvent.USER_UPDATED,
        patterns=[
            "user:profile:{user_id}",
            "user:*:{user_id}",
        ]
    ),

    CacheEvent.HEALTH_DEGRADED: CacheInvalidationRule(
        event=CacheEvent.HEALTH_DEGRADED,
        patterns=[
            "system:health",
            "dashboard:metrics:*",
        ]
    ),
}


# ============================================================================
# Cache Strategy Classes
# ============================================================================

class TTLStrategy:
    """Time-to-live based cache invalidation"""

    @staticmethod
    def get_ttl(data_type: str) -> int:
        """Get TTL for data type"""
        try:
            return CacheTTL[data_type.upper()].value
        except KeyError:
            # Default TTL: 5 minutes
            return 300


class EventStrategy:
    """Event-based cache invalidation"""

    @staticmethod
    def get_invalidation_patterns(
        event: CacheEvent,
        **kwargs
    ) -> List[str]:
        """Get cache patterns to invalidate for an event"""
        rule = INVALIDATION_RULES.get(event)
        if not rule:
            return []

        # Format patterns with event parameters
        patterns = []
        for pattern in rule.patterns:
            try:
                formatted = pattern.format(**kwargs)
                patterns.append(formatted)
            except KeyError:
                # Pattern doesn't need this parameter
                patterns.append(pattern)

        return patterns


class HybridStrategy:
    """Combines TTL and event-based invalidation"""

    def __init__(self, ttl_strategy: TTLStrategy, event_strategy: EventStrategy):
        """Initialize with both strategies"""
        self.ttl_strategy = ttl_strategy
        self.event_strategy = event_strategy

    def should_cache(self, data_type: str) -> bool:
        """Determine if data should be cached"""
        # Cache everything by default
        return True

    def get_cache_ttl(self, data_type: str) -> int:
        """Get TTL for data type"""
        return self.ttl_strategy.get_ttl(data_type)

    def handle_event(
        self,
        event: CacheEvent,
        **kwargs
    ) -> List[str]:
        """Get patterns to invalidate on event"""
        return self.event_strategy.get_invalidation_patterns(event, **kwargs)


# ============================================================================
# Singleton Strategy Instance
# ============================================================================

DEFAULT_TTL_STRATEGY = TTLStrategy()
DEFAULT_EVENT_STRATEGY = EventStrategy()
DEFAULT_HYBRID_STRATEGY = HybridStrategy(DEFAULT_TTL_STRATEGY, DEFAULT_EVENT_STRATEGY)
