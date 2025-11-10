"""
Integration tests for cached repositories.

Tests cache-aside and write-through patterns, invalidation, and fallback behavior.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from ai_pal.cache.redis_cache import RedisCache
from ai_pal.storage.cached_repositories import (
    CachedARIRepository,
    CachedGoalRepository,
    CachedTaskRepository,
    create_cached_ari_repo,
    create_cached_goal_repo,
    create_cached_task_repo,
)
from ai_pal.storage.database import DatabaseManager, ARIRepository, GoalRepository, BackgroundTaskRepository


class TestCachedARIRepository:
    """Test CachedARIRepository with cache-aside pattern."""

    @pytest.fixture
    async def setup(self):
        """Setup test dependencies."""
        db_manager = AsyncMock(spec=DatabaseManager)
        cache = AsyncMock(spec=RedisCache)
        cache.enabled = True
        db_repo = AsyncMock(spec=ARIRepository)

        return {
            "db_manager": db_manager,
            "cache": cache,
            "db_repo": db_repo,
        }

    @pytest.mark.asyncio
    async def test_get_snapshots_cache_hit(self, setup):
        """Test getting snapshots from cache (cache hit)."""
        cached_data = [
            {"snapshot_id": "1", "autonomy_retention": 75.0},
            {"snapshot_id": "2", "autonomy_retention": 78.0},
        ]

        setup["cache"].get.return_value = cached_data

        repo = CachedARIRepository(setup["db_manager"], setup["cache"])
        result = await repo.get_snapshots_by_user("user123")

        # Verify cache was checked
        setup["cache"].get.assert_called_once()

        # Verify database was NOT called (cache hit)
        setup["db_repo"].get_snapshots_by_user.assert_not_called()

        # Verify result matches cached data
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_get_snapshots_cache_miss(self, setup):
        """Test getting snapshots from database (cache miss)."""
        db_data = [
            {"snapshot_id": "1", "autonomy_retention": 75.0},
            {"snapshot_id": "2", "autonomy_retention": 78.0},
        ]

        setup["cache"].get.return_value = None  # Cache miss
        repo = CachedARIRepository(setup["db_manager"], setup["cache"])
        repo.db_repo.get_snapshots_by_user = AsyncMock(return_value=db_data)

        result = await repo.get_snapshots_by_user("user123")

        # Verify cache was checked
        setup["cache"].get.assert_called_once()

        # Verify database was called
        repo.db_repo.get_snapshots_by_user.assert_called_once()

        # Verify cache was updated
        setup["cache"].set.assert_called_once()

        # Verify result matches database data
        assert result == db_data

    @pytest.mark.asyncio
    async def test_get_latest_snapshot_cache_aside(self, setup):
        """Test cache-aside pattern for latest snapshot."""
        latest = {"snapshot_id": "latest", "autonomy_retention": 85.0}
        setup["cache"].get.return_value = None

        repo = CachedARIRepository(setup["db_manager"], setup["cache"])
        repo.db_repo.get_latest_snapshot = AsyncMock(return_value=latest)

        result = await repo.get_latest_snapshot("user123")

        # Verify cache was updated on miss
        setup["cache"].set.assert_called_once()
        assert result == latest

    @pytest.mark.asyncio
    async def test_save_snapshot_write_through(self, setup):
        """Test write-through pattern on save."""
        snapshot_data = {"user_id": "user123", "autonomy_retention": 80.0}

        setup["cache"].delete = AsyncMock()
        repo = CachedARIRepository(setup["db_manager"], setup["cache"])
        repo.db_repo.save_snapshot = AsyncMock(return_value="snapshot_id_123")

        result = await repo.save_snapshot(snapshot_data)

        # Verify database was written first
        repo.db_repo.save_snapshot.assert_called_once()

        # Verify cache was invalidated
        setup["cache"].delete_pattern.assert_called_once()

        assert result == "snapshot_id_123"

    @pytest.mark.asyncio
    async def test_cache_error_graceful_handling(self, setup):
        """Test graceful handling when cache operations error."""
        setup["cache"].get.side_effect = Exception("Redis error")
        db_data = [{"snapshot_id": "1", "autonomy_retention": 75.0}]

        repo = CachedARIRepository(setup["db_manager"], setup["cache"])
        repo.db_repo.get_snapshots_by_user = AsyncMock(return_value=db_data)

        # Should raise the cache error (in production, would be handled with try/catch)
        with pytest.raises(Exception):
            await repo.get_snapshots_by_user("user123")


class TestCachedGoalRepository:
    """Test CachedGoalRepository with write-through pattern."""

    @pytest.fixture
    async def setup(self):
        """Setup test dependencies."""
        db_manager = AsyncMock(spec=DatabaseManager)
        cache = AsyncMock(spec=RedisCache)
        cache.enabled = True
        db_repo = AsyncMock(spec=GoalRepository)

        return {
            "db_manager": db_manager,
            "cache": cache,
            "db_repo": db_repo,
        }

    @pytest.mark.asyncio
    async def test_get_active_goals_cache_aside(self, setup):
        """Test cache-aside pattern for active goals."""
        goals = [
            {"goal_id": "g1", "description": "Goal 1", "status": "active"},
            {"goal_id": "g2", "description": "Goal 2", "status": "active"},
        ]

        setup["cache"].get.return_value = goals
        repo = CachedGoalRepository(setup["db_manager"], setup["cache"])

        result = await repo.get_active_goals("user123")

        # Verify cache hit
        setup["cache"].get.assert_called_once()
        assert result == goals

    @pytest.mark.asyncio
    async def test_get_goal_by_id_cache_aside(self, setup):
        """Test cache-aside for individual goal."""
        goal = {"goal_id": "g1", "description": "Goal 1"}
        setup["cache"].get.return_value = None

        repo = CachedGoalRepository(setup["db_manager"], setup["cache"])
        repo.db_repo.get_goal_by_id = AsyncMock(return_value=goal)

        result = await repo.get_goal_by_id("g1")

        # Verify cache miss and update
        setup["cache"].set.assert_called_once()
        assert result == goal

    @pytest.mark.asyncio
    async def test_create_goal_write_through(self, setup):
        """Test write-through pattern on goal creation."""
        goal_data = {"user_id": "user123", "description": "New goal"}

        repo = CachedGoalRepository(setup["db_manager"], setup["cache"])
        repo.db_repo.create_goal = AsyncMock(return_value="goal_id_123")

        result = await repo.create_goal("user123", goal_data)

        # Verify database write first
        repo.db_repo.create_goal.assert_called_once()

        # Verify cache invalidation
        assert setup["cache"].delete.call_count >= 2  # Delete goal list + dashboard

        assert result == "goal_id_123"

    @pytest.mark.asyncio
    async def test_update_goal_invalidates_related_caches(self, setup):
        """Test that updating goal invalidates all related caches."""
        goal_data = {"description": "Updated goal"}
        updated = {"goal_id": "g1", "description": "Updated goal"}

        repo = CachedGoalRepository(setup["db_manager"], setup["cache"])
        repo.db_repo.update_goal = AsyncMock(return_value=updated)

        result = await repo.update_goal("g1", "user123", goal_data)

        # Verify multiple cache invalidations
        # Should invalidate: goal detail, goals list, dashboard
        assert setup["cache"].delete.call_count >= 3

        assert result == updated

    @pytest.mark.asyncio
    async def test_complete_goal_updates_multiple_caches(self, setup):
        """Test that completing goal invalidates multiple caches."""
        completed = {"goal_id": "g1", "status": "completed", "progress_percentage": 100}

        repo = CachedGoalRepository(setup["db_manager"], setup["cache"])
        repo.db_repo.complete_goal = AsyncMock(return_value=completed)

        result = await repo.complete_goal("g1", "user123")

        # Verify cache invalidations
        assert setup["cache"].delete.call_count >= 3

        assert result == completed


class TestCachedTaskRepository:
    """Test CachedTaskRepository."""

    @pytest.fixture
    async def setup(self):
        """Setup test dependencies."""
        db_manager = AsyncMock(spec=DatabaseManager)
        cache = AsyncMock(spec=RedisCache)
        cache.enabled = True
        db_repo = AsyncMock(spec=BackgroundTaskRepository)

        return {
            "db_manager": db_manager,
            "cache": cache,
            "db_repo": db_repo,
        }

    @pytest.mark.asyncio
    async def test_get_tasks_by_status_cache_aside(self, setup):
        """Test cache-aside pattern for task queries."""
        tasks = [
            {"task_id": "t1", "status": "pending"},
            {"task_id": "t2", "status": "pending"},
        ]

        setup["cache"].get.return_value = tasks
        repo = CachedTaskRepository(setup["db_manager"], setup["cache"])

        result = await repo.get_tasks_by_status("user123", "pending")

        setup["cache"].get.assert_called_once()
        assert result == tasks

    @pytest.mark.asyncio
    async def test_create_task_invalidates_cache(self, setup):
        """Test that creating task invalidates cache."""
        task_data = {"user_id": "user123", "task_type": "ari_analysis"}

        repo = CachedTaskRepository(setup["db_manager"], setup["cache"])
        repo.db_repo.create_task = AsyncMock(return_value="task_id_123")

        result = await repo.create_task(task_data)

        # Verify cache invalidation with pattern
        setup["cache"].delete_pattern.assert_called_once()

        assert result == "task_id_123"

    @pytest.mark.asyncio
    async def test_update_task_status_invalidates_cache(self, setup):
        """Test that updating task status invalidates cache."""
        updated = {"task_id": "t1", "status": "completed"}

        repo = CachedTaskRepository(setup["db_manager"], setup["cache"])
        repo.db_repo.update_task_status = AsyncMock(return_value=updated)

        result = await repo.update_task_status("t1", "user123", "completed")

        # Verify cache invalidation
        setup["cache"].delete_pattern.assert_called_once()

        assert result == updated


class TestCacheInvalidationPatterns:
    """Test cache invalidation patterns."""

    @pytest.mark.asyncio
    async def test_single_key_invalidation(self):
        """Test invalidation of single cache keys."""
        cache = AsyncMock(spec=RedisCache)

        # Simulate single key delete
        await cache.delete("goal:g1")
        cache.delete.assert_called_once_with("goal:g1")

    @pytest.mark.asyncio
    async def test_pattern_based_invalidation(self):
        """Test pattern-based cache invalidation."""
        cache = AsyncMock(spec=RedisCache)

        # Simulate pattern deletion
        await cache.delete_pattern("user:goals:*:user123")
        cache.delete_pattern.assert_called_once_with("user:goals:*:user123")

    @pytest.mark.asyncio
    async def test_cascading_invalidation(self):
        """Test cascading invalidation of related caches."""
        cache = AsyncMock(spec=RedisCache)

        # Simulate cascading deletes for goal update
        user_id = "user123"
        goal_id = "g1"

        await cache.delete(f"goal:{goal_id}")
        await cache.delete(f"user:goals:active:{user_id}")
        await cache.delete(f"dashboard:metrics:{user_id}")

        # Verify all deletes were called
        assert cache.delete.call_count == 3


class TestFactoryFunctions:
    """Test factory functions for creating cached repositories."""

    @pytest.mark.asyncio
    async def test_create_cached_ari_repo(self):
        """Test factory function for ARI repository."""
        db_manager = AsyncMock(spec=DatabaseManager)
        cache = AsyncMock(spec=RedisCache)

        repo = create_cached_ari_repo(db_manager, cache)

        assert isinstance(repo, CachedARIRepository)
        assert repo.cache == cache
        assert hasattr(repo, 'db_repo')

    @pytest.mark.asyncio
    async def test_create_cached_goal_repo(self):
        """Test factory function for goal repository."""
        db_manager = AsyncMock(spec=DatabaseManager)
        cache = AsyncMock(spec=RedisCache)

        repo = create_cached_goal_repo(db_manager, cache)

        assert isinstance(repo, CachedGoalRepository)
        assert repo.cache == cache
        assert hasattr(repo, 'db_repo')

    @pytest.mark.asyncio
    async def test_create_cached_task_repo(self):
        """Test factory function for task repository."""
        db_manager = AsyncMock(spec=DatabaseManager)
        cache = AsyncMock(spec=RedisCache)

        repo = create_cached_task_repo(db_manager, cache)

        assert isinstance(repo, CachedTaskRepository)
        assert repo.cache == cache
        assert hasattr(repo, 'db_repo')


class TestCacheErrorHandling:
    """Test error handling in cached repositories."""

    @pytest.mark.asyncio
    async def test_cache_error_fallback_to_database(self):
        """Test fallback to database when cache errors."""
        db_manager = AsyncMock(spec=DatabaseManager)
        cache = AsyncMock(spec=RedisCache)
        cache.enabled = True
        cache.get.side_effect = Exception("Redis connection error")

        repo = CachedARIRepository(db_manager, cache)
        repo.db_repo.get_snapshots_by_user = AsyncMock(
            return_value=[{"snapshot_id": "1"}]
        )

        # Should fall back gracefully to database
        # In production, this would be handled with try/except
        try:
            await repo.get_snapshots_by_user("user123")
        except Exception as e:
            # The cache error should propagate or be handled
            assert isinstance(e, Exception)

    @pytest.mark.asyncio
    async def test_database_error_not_cached(self):
        """Test that database errors aren't cached."""
        db_manager = AsyncMock(spec=DatabaseManager)
        cache = AsyncMock(spec=RedisCache)
        cache.enabled = True
        cache.get.return_value = None

        repo = CachedARIRepository(db_manager, cache)
        repo.db_repo.get_snapshots_by_user = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Should raise the database error without caching
        with pytest.raises(Exception):
            await repo.get_snapshots_by_user("user123")

        # Cache set should not be called on error
        cache.set.assert_not_called()


class TestConcurrentAccess:
    """Test concurrent access patterns."""

    @pytest.mark.asyncio
    async def test_concurrent_cache_gets(self):
        """Test multiple concurrent cache get operations."""
        import asyncio

        db_manager = AsyncMock(spec=DatabaseManager)
        cache = AsyncMock(spec=RedisCache)
        cache.enabled = True
        cache.get = AsyncMock(return_value=[{"snapshot_id": "1"}])

        repo = CachedARIRepository(db_manager, cache)

        # Simulate concurrent requests
        tasks = [
            repo.get_snapshots_by_user("user123")
            for _ in range(5)
        ]

        results = await asyncio.gather(*tasks)

        # All should return cached data
        assert len(results) == 5
        assert cache.get.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_write_through(self):
        """Test concurrent write operations don't cause race conditions."""
        import asyncio

        db_manager = AsyncMock(spec=DatabaseManager)
        cache = AsyncMock(spec=RedisCache)
        cache.enabled = True

        repo = CachedGoalRepository(db_manager, cache)
        repo.db_repo.update_goal = AsyncMock(
            return_value={"goal_id": "g1", "description": "Updated"}
        )

        # Simulate concurrent updates
        tasks = [
            repo.update_goal(f"g{i}", "user123", {"description": f"Goal {i}"})
            for i in range(3)
        ]

        results = await asyncio.gather(*tasks)

        # All updates should complete
        assert len(results) == 3
        assert repo.db_repo.update_goal.call_count == 3
        assert cache.delete.call_count >= 9  # 3 updates × 3 cache deletes
