"""
Storage Module - Database, Cache, and Background Jobs

Provides unified storage layer with:
- Database backend (SQLite/PostgreSQL)
- Redis caching
- Background job processing
- Repository pattern for data access

Usage:
    from ai_pal.storage import StorageBackend

    # Initialize storage
    storage = await StorageBackend.create(
        database_url="postgresql+asyncpg://user:pass@localhost/ai_pal",
        redis_url="redis://localhost:6379/0",
        enable_cache=True,
        enable_background_jobs=True
    )

    # Use repositories
    profile = await storage.users.get_profile("user123")
    await storage.ari.save_snapshot(snapshot_data)

    # Shutdown
    await storage.close()
"""

from typing import Optional
from pathlib import Path

from loguru import logger

from .database import (
    DatabaseManager,
    ARIRepository,
    GoalRepository,
    UserProfileRepository
)
from ..cache.redis_cache import RedisCache, UserDataCache
from ..tasks.background_jobs import TaskQueue, TaskScheduler


class StorageBackend:
    """
    Unified storage backend

    Manages database, cache, and background jobs
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        cache: Optional[RedisCache] = None,
        task_queue: Optional[TaskQueue] = None,
        scheduler: Optional[TaskScheduler] = None
    ):
        """
        Initialize storage backend

        Args:
            db_manager: Database manager
            cache: Redis cache (optional)
            task_queue: Background task queue (optional)
            scheduler: Task scheduler (optional)
        """
        self.db = db_manager
        self.cache = cache
        self.task_queue = task_queue
        self.scheduler = scheduler

        # Create repositories
        self.ari = ARIRepository(db_manager)
        self.goals = GoalRepository(db_manager)
        self.users = UserProfileRepository(db_manager)

        # Create cache managers
        if cache:
            self.user_cache = UserDataCache(cache)
        else:
            self.user_cache = None

        logger.info("StorageBackend initialized")

    @classmethod
    async def create(
        cls,
        database_url: str = "sqlite+aiosqlite:///./ai_pal.db",
        redis_url: Optional[str] = "redis://localhost:6379/0",
        enable_cache: bool = True,
        enable_background_jobs: bool = True,
        create_tables: bool = True,
        max_workers: int = 5
    ) -> "StorageBackend":
        """
        Create and initialize storage backend

        Args:
            database_url: Database URL
            redis_url: Redis URL (None to disable caching)
            enable_cache: Enable Redis caching
            enable_background_jobs: Enable background job processing
            create_tables: Create database tables if they don't exist
            max_workers: Max background job workers

        Returns:
            Initialized StorageBackend
        """
        # Create database manager
        db_manager = DatabaseManager(database_url=database_url)

        # Create tables if requested
        if create_tables:
            await db_manager.create_tables()

        # Create cache if enabled
        cache = None
        if enable_cache and redis_url:
            cache = RedisCache(redis_url=redis_url)
            # Test connection
            if not await cache.ping():
                logger.warning("Redis connection failed, caching disabled")
                cache = None

        # Create task queue if enabled
        task_queue = None
        if enable_background_jobs:
            task_queue = TaskQueue(max_workers=max_workers)
            await task_queue.start()

        # Create scheduler if enabled
        scheduler = None
        if enable_background_jobs:
            scheduler = TaskScheduler()
            # Scheduler will be started separately after tasks are added

        return cls(
            db_manager=db_manager,
            cache=cache,
            task_queue=task_queue,
            scheduler=scheduler
        )

    async def close(self):
        """Close all connections and shutdown background tasks"""
        # Shutdown background jobs
        if self.task_queue:
            await self.task_queue.shutdown(wait=True)

        if self.scheduler:
            await self.scheduler.stop()

        # Close cache
        if self.cache:
            await self.cache.close()

        # Close database
        await self.db.close()

        logger.info("StorageBackend closed")

    async def health_check(self) -> dict:
        """
        Check health of all storage components

        Returns:
            Health status dict
        """
        health = {
            "database": "unknown",
            "cache": "unknown",
            "task_queue": "unknown",
            "scheduler": "unknown"
        }

        # Check database
        try:
            async with self.db.get_session() as session:
                # Simple query to test connection
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
                health["database"] = "healthy"
        except Exception as e:
            health["database"] = f"unhealthy: {str(e)}"

        # Check cache
        if self.cache:
            if await self.cache.ping():
                health["cache"] = "healthy"
            else:
                health["cache"] = "unhealthy"
        else:
            health["cache"] = "disabled"

        # Check task queue
        if self.task_queue:
            stats = await self.task_queue.get_stats()
            if stats["running"]:
                health["task_queue"] = f"healthy ({stats['workers']} workers, {stats['pending']} pending)"
            else:
                health["task_queue"] = "stopped"
        else:
            health["task_queue"] = "disabled"

        # Check scheduler
        if self.scheduler:
            if self.scheduler.running:
                health["scheduler"] = f"healthy ({len(self.scheduler.tasks)} tasks)"
            else:
                health["scheduler"] = "stopped"
        else:
            health["scheduler"] = "disabled"

        return health


# Re-export key classes for convenience
__all__ = [
    "StorageBackend",
    "DatabaseManager",
    "ARIRepository",
    "GoalRepository",
    "UserProfileRepository",
    "RedisCache",
    "UserDataCache",
    "TaskQueue",
    "TaskScheduler"
]
