"""
Cache Health Monitoring

Provides health checks and metrics for Redis caching layer.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import time

from loguru import logger

from ai_pal.cache.redis_cache import RedisCache


@dataclass
class CacheMetrics:
    """Cache performance metrics"""

    redis_connected: bool
    response_time_ms: float
    memory_used_mb: Optional[float]
    keys_count: int
    hit_rate: float
    evictions_per_minute: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class CacheHealthChecker:
    """Monitors cache health and performance"""

    def __init__(self, cache: RedisCache):
        """Initialize health checker"""
        self.cache = cache
        self.last_hit_count = 0
        self.last_miss_count = 0
        self.last_evictions = 0
        self.last_check_time = time.time()

    async def check_health(self) -> CacheMetrics:
        """Perform health check"""
        # Test connection
        connected = await self.cache.ping()

        response_time_ms = 0.0
        memory_used_mb = None
        keys_count = 0
        hit_rate = 0.0
        evictions_per_minute = 0.0

        if connected and self.cache.enabled and self.cache.client:
            try:
                # Measure response time
                start = time.time()
                await self.cache.client.ping()
                response_time_ms = (time.time() - start) * 1000

                # Get memory usage
                info = await self.cache.client.info()
                memory_used_mb = info.get("used_memory", 0) / (1024 * 1024)
                keys_count = info.get("db0", {}).get("keys", 0) if "db0" in info else 0

                # Calculate hit rate
                hits = info.get("keyspace_hits", 0)
                misses = info.get("keyspace_misses", 0)
                total = hits + misses
                hit_rate = (hits / total) if total > 0 else 0

                # Calculate evictions
                evictions = info.get("evicted_keys", 0)
                current_time = time.time()
                time_delta = current_time - self.last_check_time
                if time_delta > 0:
                    evictions_per_minute = ((evictions - self.last_evictions) / time_delta) * 60

                self.last_check_time = current_time
                self.last_evictions = evictions

            except Exception as e:
                logger.warning(f"Error getting cache metrics: {e}")

        metrics = CacheMetrics(
            redis_connected=connected,
            response_time_ms=response_time_ms,
            memory_used_mb=memory_used_mb,
            keys_count=keys_count,
            hit_rate=hit_rate,
            evictions_per_minute=evictions_per_minute,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

        return metrics

    async def is_healthy(self) -> bool:
        """Check if cache is healthy"""
        metrics = await self.check_health()

        # Healthy if:
        # - Connected
        # - Response time < 10ms
        # - Memory < 90% usage (if available)
        if not metrics.redis_connected:
            return False

        if metrics.response_time_ms > 10:
            logger.warning(f"Cache response time degraded: {metrics.response_time_ms}ms")
            return False

        return True

    async def get_status_string(self) -> str:
        """Get human-readable health status"""
        metrics = await self.check_health()

        status_parts = []

        # Connection status
        if metrics.redis_connected:
            status_parts.append("✓ Redis Connected")
        else:
            status_parts.append("✗ Redis Disconnected")

        # Response time
        status_parts.append(f"Response Time: {metrics.response_time_ms:.1f}ms")

        # Memory
        if metrics.memory_used_mb:
            status_parts.append(f"Memory: {metrics.memory_used_mb:.1f}MB")

        # Keys
        status_parts.append(f"Keys: {metrics.keys_count}")

        # Hit rate
        status_parts.append(f"Hit Rate: {metrics.hit_rate * 100:.1f}%")

        # Evictions
        if metrics.evictions_per_minute > 0:
            status_parts.append(f"⚠ Evictions: {metrics.evictions_per_minute:.1f}/min")

        return " | ".join(status_parts)


class CacheStatistics:
    """Tracks cache statistics"""

    def __init__(self):
        """Initialize statistics"""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0

    def record_hit(self):
        """Record cache hit"""
        self.hits += 1

    def record_miss(self):
        """Record cache miss"""
        self.misses += 1

    def record_set(self):
        """Record cache set"""
        self.sets += 1

    def record_delete(self):
        """Record cache delete"""
        self.deletes += 1

    def record_error(self):
        """Record cache error"""
        self.errors += 1

    def get_hit_rate(self) -> float:
        """Get cache hit rate"""
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "hit_rate": self.get_hit_rate(),
        }

    def reset(self):
        """Reset statistics"""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0


# Singleton statistics instance
_cache_stats = CacheStatistics()


def get_cache_stats() -> CacheStatistics:
    """Get cache statistics"""
    return _cache_stats
