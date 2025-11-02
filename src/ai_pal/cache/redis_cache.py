"""
Redis Caching Layer

Provides high-performance caching for:
- Frequently accessed user profiles
- Recent ARI snapshots
- Active goals and blocks
- Personality data
- Model responses (optional)

Features:
- TTL-based expiration
- Cache warming
- Cache invalidation
- Async operations
- Connection pooling
- Graceful fallback when Redis unavailable
"""

from datetime import timedelta
from typing import Optional, Any, Dict, List
import json
import hashlib
from functools import wraps

from loguru import logger

# Optional Redis dependency
try:
    import redis.asyncio as redis
    from redis.asyncio import Redis, ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis not installed. Run: pip install redis")


class CacheKey:
    """Cache key templates"""

    # User data
    USER_PROFILE = "user:profile:{user_id}"
    USER_ARI_LATEST = "user:ari:latest:{user_id}"
    USER_ARI_HISTORY = "user:ari:history:{user_id}:{days}"
    USER_GOALS_ACTIVE = "user:goals:active:{user_id}"
    USER_STRENGTHS = "user:strengths:{user_id}"

    # FFE data
    GOAL_DETAILS = "goal:{goal_id}"
    GOAL_BLOCKS = "goal:blocks:{goal_id}"
    MOMENTUM_STATE = "momentum:state:{user_id}"

    # Dashboard data
    PROGRESS_TAPESTRY = "tapestry:{user_id}:{days}"
    DASHBOARD_METRICS = "dashboard:metrics:{user_id}"

    # Model responses (optional - can be very large)
    MODEL_RESPONSE = "model:response:{hash}"


class RedisCache:
    """Redis cache manager"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 300,  # 5 minutes
        max_connections: int = 10,
        enabled: bool = True
    ):
        """
        Initialize Redis cache

        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds
            max_connections: Max connections in pool
            enabled: Enable caching (set to False to disable)
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.enabled = enabled and REDIS_AVAILABLE

        if not REDIS_AVAILABLE:
            logger.warning("Redis caching disabled: redis package not installed")
            self.enabled = False
            self.client = None
            return

        if not self.enabled:
            logger.info("Redis caching disabled by configuration")
            self.client = None
            return

        # Create connection pool
        self.pool = ConnectionPool.from_url(
            redis_url,
            max_connections=max_connections,
            decode_responses=True  # Automatically decode bytes to strings
        )

        # Create client
        self.client = Redis(connection_pool=self.pool)

        logger.info(f"Redis cache initialized: {redis_url}")

    async def ping(self) -> bool:
        """
        Test Redis connection

        Returns:
            True if connected, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            await self.client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis ping failed: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.enabled or not self.client:
            return None

        try:
            value = await self.client.get(key)
            if value is not None:
                # Try to deserialize JSON
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    # Not JSON, return as-is
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            # Serialize to JSON if needed
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            # Set with TTL
            ttl = ttl or self.default_ttl
            await self.client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.client:
            return 0

        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await self.client.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.error(f"Redis delete_pattern error for pattern {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            return bool(await self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for key

        Args:
            key: Cache key

        Returns:
            TTL in seconds, None if key doesn't exist or no TTL
        """
        if not self.enabled or not self.client:
            return None

        try:
            ttl = await self.client.ttl(key)
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.error(f"Redis get_ttl error for key {key}: {e}")
            return None

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment counter

        Args:
            key: Counter key
            amount: Amount to increment

        Returns:
            New value or None on error
        """
        if not self.enabled or not self.client:
            return None

        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis increment error for key {key}: {e}")
            return None

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values at once

        Args:
            keys: List of cache keys

        Returns:
            Dict of key -> value (only for keys that exist)
        """
        if not self.enabled or not self.client or not keys:
            return {}

        try:
            values = await self.client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            return result
        except Exception as e:
            logger.error(f"Redis get_many error: {e}")
            return {}

    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set multiple values at once

        Args:
            items: Dict of key -> value
            ttl: TTL in seconds (applies to all keys)

        Returns:
            True if successful
        """
        if not self.enabled or not self.client or not items:
            return False

        try:
            # Serialize values
            serialized = {}
            for key, value in items.items():
                if isinstance(value, (dict, list)):
                    serialized[key] = json.dumps(value)
                else:
                    serialized[key] = value

            # Use pipeline for efficiency
            async with self.client.pipeline() as pipe:
                for key, value in serialized.items():
                    ttl_val = ttl or self.default_ttl
                    pipe.setex(key, ttl_val, value)
                await pipe.execute()

            return True
        except Exception as e:
            logger.error(f"Redis set_many error: {e}")
            return False

    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")

    @staticmethod
    def hash_key(data: str) -> str:
        """
        Generate hash for cache key

        Args:
            data: Data to hash

        Returns:
            SHA256 hash
        """
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# ============================================================================
# Caching Decorators
# ============================================================================

def cached(
    cache: RedisCache,
    key_template: str,
    ttl: Optional[int] = None,
    key_args: Optional[List[str]] = None
):
    """
    Decorator to cache function results

    Usage:
        @cached(redis_cache, CacheKey.USER_PROFILE, ttl=600, key_args=["user_id"])
        async def get_user_profile(user_id: str):
            # Expensive database query
            return profile

    Args:
        cache: RedisCache instance
        key_template: Key template with {arg_name} placeholders
        ttl: Cache TTL in seconds
        key_args: List of argument names to use in key (if None, uses all)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function arguments
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Extract key arguments
            if key_args:
                key_values = {k: bound.arguments[k] for k in key_args if k in bound.arguments}
            else:
                key_values = bound.arguments

            # Format cache key
            try:
                cache_key = key_template.format(**key_values)
            except KeyError as e:
                logger.warning(f"Cache key formatting failed: {e}")
                # Fall through to execute function
                return await func(*args, **kwargs)

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # Execute function
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None:
                await cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


# ============================================================================
# Specialized Cache Managers
# ============================================================================

class UserDataCache:
    """Cache manager for user data"""

    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache

    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user profile"""
        key = CacheKey.USER_PROFILE.format(user_id=user_id)
        return await self.cache.get(key)

    async def set_profile(self, user_id: str, profile: Dict[str, Any], ttl: int = 600):
        """Cache user profile"""
        key = CacheKey.USER_PROFILE.format(user_id=user_id)
        await self.cache.set(key, profile, ttl=ttl)

    async def invalidate_profile(self, user_id: str):
        """Invalidate user profile cache"""
        key = CacheKey.USER_PROFILE.format(user_id=user_id)
        await self.cache.delete(key)

    async def get_latest_ari(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached latest ARI snapshot"""
        key = CacheKey.USER_ARI_LATEST.format(user_id=user_id)
        return await self.cache.get(key)

    async def set_latest_ari(self, user_id: str, snapshot: Dict[str, Any], ttl: int = 300):
        """Cache latest ARI snapshot"""
        key = CacheKey.USER_ARI_LATEST.format(user_id=user_id)
        await self.cache.set(key, snapshot, ttl=ttl)

    async def get_active_goals(self, user_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached active goals"""
        key = CacheKey.USER_GOALS_ACTIVE.format(user_id=user_id)
        return await self.cache.get(key)

    async def set_active_goals(self, user_id: str, goals: List[Dict[str, Any]], ttl: int = 300):
        """Cache active goals"""
        key = CacheKey.USER_GOALS_ACTIVE.format(user_id=user_id)
        await self.cache.set(key, goals, ttl=ttl)

    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cache for a user"""
        pattern = f"user:*:{user_id}"
        deleted = await self.cache.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted} cache keys for user {user_id}")


class ModelResponseCache:
    """Cache manager for model responses (optional)"""

    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache

    async def get_response(self, prompt: str, model: str) -> Optional[str]:
        """
        Get cached model response

        Args:
            prompt: The prompt
            model: Model name

        Returns:
            Cached response or None
        """
        # Create cache key from prompt + model
        cache_data = f"{model}:{prompt}"
        key_hash = RedisCache.hash_key(cache_data)
        key = CacheKey.MODEL_RESPONSE.format(hash=key_hash)

        return await self.cache.get(key)

    async def set_response(
        self,
        prompt: str,
        model: str,
        response: str,
        ttl: int = 3600  # 1 hour default
    ):
        """
        Cache model response

        Args:
            prompt: The prompt
            model: Model name
            response: Model response
            ttl: Cache TTL
        """
        cache_data = f"{model}:{prompt}"
        key_hash = RedisCache.hash_key(cache_data)
        key = CacheKey.MODEL_RESPONSE.format(hash=key_hash)

        await self.cache.set(key, response, ttl=ttl)
