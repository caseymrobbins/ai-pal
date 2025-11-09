"""
Cached Repository Layer

Wraps database repositories with Redis caching to reduce database load.
Implements cache-aside pattern for reads and write-through for critical data.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from loguru import logger

from ai_pal.cache.redis_cache import RedisCache, CacheKey
from ai_pal.storage.database import (
    DatabaseManager,
    ARIRepository,
    GoalRepository,
    BackgroundTaskRepository,
)


class CachedARIRepository:
    """ARI repository with Redis caching"""

    def __init__(self, db_manager: DatabaseManager, cache: RedisCache):
        """Initialize with database and cache"""
        self.db_repo = ARIRepository(db_manager)
        self.cache = cache

    async def get_snapshots_by_user(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get ARI snapshots with caching (cache-aside pattern)"""
        # Generate cache key
        cache_key = CacheKey.USER_ARI_HISTORY.format(user_id=user_id, days=30)

        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache hit: {cache_key}")
            return cached

        # Cache miss - fetch from database
        logger.debug(f"Cache miss: {cache_key}")
        snapshots = await self.db_repo.get_snapshots_by_user(
            user_id, start_date, end_date, limit
        )

        # Update cache (5 minute TTL for ARI data)
        await self.cache.set(cache_key, snapshots, ttl=300)

        return snapshots

    async def get_latest_snapshot(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get latest ARI snapshot with caching"""
        cache_key = CacheKey.USER_ARI_LATEST.format(user_id=user_id)

        # Try cache
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        snapshot = await self.db_repo.get_latest_snapshot(user_id)

        # Cache if found (5 minute TTL)
        if snapshot:
            await self.cache.set(cache_key, snapshot, ttl=300)

        return snapshot

    async def save_snapshot(self, snapshot_data: Dict[str, Any]) -> str:
        """Save snapshot and invalidate cache (write-through pattern)"""
        user_id = snapshot_data.get("user_id")

        # Write to database
        snapshot_id = await self.db_repo.save_snapshot(snapshot_data)

        # Invalidate cache for this user
        if user_id:
            await self.cache.delete_pattern(f"user:ari:*:{user_id}")
            logger.info(f"Invalidated ARI cache for user {user_id}")

        return snapshot_id


class CachedGoalRepository:
    """Goal repository with Redis caching"""

    def __init__(self, db_manager: DatabaseManager, cache: RedisCache):
        """Initialize with database and cache"""
        self.db_repo = GoalRepository(db_manager)
        self.cache = cache

    async def get_active_goals(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get active goals with caching"""
        cache_key = CacheKey.USER_GOALS_ACTIVE.format(user_id=user_id)

        # Try cache
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        goals = await self.db_repo.get_active_goals(user_id, limit)

        # Cache (10 minute TTL for goals)
        await self.cache.set(cache_key, goals, ttl=600)

        return goals

    async def get_goal_by_id(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get goal by ID with caching"""
        cache_key = CacheKey.GOAL_DETAILS.format(goal_id=goal_id)

        # Try cache
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        goal = await self.db_repo.get_goal_by_id(goal_id)

        # Cache if found (10 minute TTL)
        if goal:
            await self.cache.set(cache_key, goal, ttl=600)

        return goal

    async def create_goal(
        self,
        user_id: str,
        goal_data: Dict[str, Any]
    ) -> str:
        """Create goal and invalidate cache (write-through)"""
        # Write to database
        goal_id = await self.db_repo.create_goal(user_id, goal_data)

        # Invalidate goal list cache for this user
        await self.cache.delete(CacheKey.USER_GOALS_ACTIVE.format(user_id=user_id))
        await self.cache.delete(CacheKey.DASHBOARD_METRICS.format(user_id=user_id))
        logger.info(f"Invalidated goal cache for user {user_id}")

        return goal_id

    async def update_goal(
        self,
        goal_id: str,
        user_id: str,
        goal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update goal and invalidate cache (write-through)"""
        # Write to database
        updated = await self.db_repo.update_goal(goal_id, user_id, goal_data)

        # Invalidate related caches
        await self.cache.delete(CacheKey.GOAL_DETAILS.format(goal_id=goal_id))
        await self.cache.delete(CacheKey.USER_GOALS_ACTIVE.format(user_id=user_id))
        await self.cache.delete(CacheKey.DASHBOARD_METRICS.format(user_id=user_id))
        logger.info(f"Invalidated goal cache for goal {goal_id}")

        return updated

    async def complete_goal(self, goal_id: str, user_id: str) -> Dict[str, Any]:
        """Complete goal and invalidate cache"""
        # Write to database
        completed = await self.db_repo.complete_goal(goal_id, user_id)

        # Invalidate related caches
        await self.cache.delete(CacheKey.GOAL_DETAILS.format(goal_id=goal_id))
        await self.cache.delete(CacheKey.USER_GOALS_ACTIVE.format(user_id=user_id))
        await self.cache.delete(CacheKey.DASHBOARD_METRICS.format(user_id=user_id))
        logger.info(f"Invalidated goal cache for user {user_id}")

        return completed


class CachedTaskRepository:
    """Background task repository with Redis caching"""

    def __init__(self, db_manager: DatabaseManager, cache: RedisCache):
        """Initialize with database and cache"""
        self.db_repo = BackgroundTaskRepository(db_manager)
        self.cache = cache

    async def get_tasks_by_status(
        self,
        user_id: str,
        status: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get tasks with caching"""
        cache_key = f"user:tasks:{user_id}:{status}"

        # Try cache
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from database
        tasks = await self.db_repo.get_tasks_by_status(user_id, status, limit)

        # Cache (2 minute TTL for tasks as they change frequently)
        await self.cache.set(cache_key, tasks, ttl=120)

        return tasks

    async def create_task(self, task_data: Dict[str, Any]) -> str:
        """Create task and invalidate cache"""
        user_id = task_data.get("user_id")

        # Write to database
        task_id = await self.db_repo.create_task(task_data)

        # Invalidate task caches for this user
        if user_id:
            await self.cache.delete_pattern(f"user:tasks:{user_id}:*")
            logger.info(f"Invalidated task cache for user {user_id}")

        return task_id

    async def update_task_status(
        self,
        task_id: str,
        user_id: str,
        status: str
    ) -> Dict[str, Any]:
        """Update task status and invalidate cache"""
        # Write to database
        updated = await self.db_repo.update_task_status(task_id, user_id, status)

        # Invalidate task caches
        await self.cache.delete_pattern(f"user:tasks:{user_id}:*")
        logger.info(f"Invalidated task cache for user {user_id}")

        return updated


# ============================================================================
# Factory Functions for Easy Integration
# ============================================================================

def create_cached_ari_repo(
    db_manager: DatabaseManager,
    cache: RedisCache
) -> CachedARIRepository:
    """Create cached ARI repository"""
    return CachedARIRepository(db_manager, cache)


def create_cached_goal_repo(
    db_manager: DatabaseManager,
    cache: RedisCache
) -> CachedGoalRepository:
    """Create cached goal repository"""
    return CachedGoalRepository(db_manager, cache)


def create_cached_task_repo(
    db_manager: DatabaseManager,
    cache: RedisCache
) -> CachedTaskRepository:
    """Create cached task repository"""
    return CachedTaskRepository(db_manager, cache)
